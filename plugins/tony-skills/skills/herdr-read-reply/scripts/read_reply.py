"""讀取 Herdr App 終端機裡 Claude 或 Codex 最近完成的回合，把回覆原文寫進 UTF-8 檔案。

回覆一律寫檔不印到 stdout：Windows 主控台會把中文轉成亂碼，也避免整段回覆直接灌進呼叫端。
stdout 只印一行 JSON，status 不是 ok 時改用 hc read 讀畫面。

用法：
  python read_reply.py --target <位址或名稱> --out <輸出檔> [--turns 1]

status：
  ok           已寫入 out；running 為 true 表示紀錄裡還有未完成的回合，寫入的是它之前完成的回合
  busy         對方 working 或 blocked，先 hc wait 再重跑
  no_session   找不到這個終端機對應的 session，或 Codex 有多個候選無法分辨
  not_found    找不到紀錄檔，或紀錄裡沒有完成的回合
  stale        Claude 的紀錄檔標題與終端機標題不同，找到的 session 已不是目前的對話
  unsupported  不是 Claude 或 Codex
  error        hc 指令或解析失敗，message 有原因
"""
import argparse
import datetime
import glob
import json
import os
import re
import subprocess
import sys

PROMPT_LIMIT = 1500
AGENT_KINDS = {"claude-code": "claude", "codex": "codex"}
# Claude 還沒替對話取標題時的預設終端機標題，無法用來比對
GENERIC_TITLES = {"", "claude", "Claude Code"}
# Codex 的 rollout 開始時間可能略早於 hc 記錄的終端機建立時間
CODEX_START_TOLERANCE_SEC = 5


def hc_get(target):
    result = subprocess.run(["hc", "get", target], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip())
    return json.loads(result.stdout)


def child_processes():
    """回傳 {父程序 pid: [子程序 pid]}。"""
    if os.name == "nt":
        script = 'Get-CimInstance Win32_Process | ForEach-Object { "$($_.ParentProcessId) $($_.ProcessId)" }'
        command = ["powershell", "-NoProfile", "-Command", script]
    else:
        command = ["ps", "-eo", "ppid=,pid="]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    children = {}
    for line in result.stdout.splitlines():
        fields = line.replace(",", " ").split()
        if len(fields) == 2 and all(f.isdigit() for f in fields):
            children.setdefault(int(fields[0]), []).append(int(fields[1]))
    return children


def claude_root():
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def claude_session_of_pid(pid):
    try:
        with open(os.path.join(claude_root(), "sessions", f"{pid}.json"), encoding="utf-8") as f:
            return json.load(f).get("sessionId")
    except (OSError, ValueError):
        return None


def claude_session_id(info):
    """Claude 可能是終端機的主程式，也可能由 shell 啟動，所以連子程序一起找。"""
    roots = [p for p in ((info.get("foreground") or {}).get("pid"), info.get("pid")) if p]
    for pid in roots:
        session_id = claude_session_of_pid(pid)
        if session_id:
            return session_id

    children = child_processes()
    queue, seen = list(roots), set()
    while queue:
        pid = queue.pop(0)
        if pid in seen:
            continue
        seen.add(pid)
        session_id = claude_session_of_pid(pid)
        if session_id:
            return session_id
        queue.extend(children.get(pid, []))
    return None


def read_jsonl(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                # 對方仍在寫入時，最後一行可能還不完整
                continue


def claude_transcript(session_id):
    hits = glob.glob(os.path.join(claude_root(), "projects", "*", session_id + ".jsonl"))
    return hits[0] if hits else None


def claude_title(path):
    title = None
    for entry in read_jsonl(path):
        if entry.get("type") == "ai-title":
            title = entry.get("aiTitle")
    return title


def claude_prompt_text(entry):
    if entry.get("isMeta"):
        return None
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = [b.get("text", "") for b in content if b.get("type") == "text"]
        return "\n".join(texts) if texts else None
    return None


def claude_turns(path):
    """以 system/turn_duration 切回合；回傳 (完成的回合, 最後是否還有未完成的回合)。"""
    turns, prompts, replies, pending = [], [], [], False
    for entry in read_jsonl(path):
        if entry.get("isSidechain"):
            continue
        kind = entry.get("type")
        if kind == "system" and entry.get("subtype") == "turn_duration":
            if replies:
                turns.append((prompts, replies))
            prompts, replies, pending = [], [], False
        elif kind == "user":
            text = claude_prompt_text(entry)
            if text is not None:
                prompts.append(text)
        elif kind == "assistant":
            content = (entry.get("message") or {}).get("content")
            if isinstance(content, list):
                pending = True
                replies.extend(b["text"] for b in content if b.get("type") == "text" and b.get("text"))
    return turns, pending


def codex_rollouts(info):
    """找出在這個終端機建立後、於同一目錄啟動的互動式 Codex 紀錄。"""
    root = os.environ.get("CODEX_HOME") or os.path.join(os.path.expanduser("~"), ".codex")
    created = info["created_ms"] / 1000
    cwd = os.path.normcase((info.get("foreground") or {}).get("cwd") or info.get("cwd") or "")
    hits = []
    for path in glob.glob(os.path.join(root, "sessions", "**", "rollout-*.jsonl"), recursive=True):
        if os.path.getmtime(path) < created:
            continue
        payload = (next(read_jsonl(path), None) or {}).get("payload") or {}
        if payload.get("originator") != "codex-tui" or os.path.normcase(payload.get("cwd") or "") != cwd:
            continue
        try:
            started = datetime.datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00")).timestamp()
        except (KeyError, ValueError):
            continue
        if started >= created - CODEX_START_TOLERANCE_SEC:
            hits.append((path, payload.get("id")))
    return hits


def codex_turns(path):
    """以 task_started／task_complete 切回合；最終回覆取 task_complete 的 last_agent_message。"""
    turns, prompts, finals, pending = [], [], [], False
    for entry in read_jsonl(path):
        payload = entry.get("payload") or {}
        kind = entry.get("type")
        ptype = payload.get("type")
        if kind == "event_msg" and ptype == "task_started":
            prompts, finals, pending = [], [], True
        elif kind == "event_msg" and ptype == "task_complete":
            reply = payload.get("last_agent_message") or "\n\n".join(finals)
            if reply:
                turns.append((prompts, [reply]))
            pending = False
        elif kind == "event_msg" and ptype == "turn_aborted":
            pending = False
        elif kind == "response_item" and ptype == "message":
            texts = [c.get("text", "") for c in payload.get("content") or [] if c.get("type") in ("input_text", "output_text")]
            if payload.get("role") == "user":
                prompts.append("\n".join(texts))
            elif payload.get("role") == "assistant" and payload.get("phase") == "final_answer":
                finals.append("".join(texts))
    return turns, pending


def write_turns(out, turns, include_prompts):
    parts = []
    for prompts, replies in turns:
        if include_prompts:
            prompt = "\n\n".join(prompts)
            if len(prompt) > PROMPT_LIMIT:
                prompt = prompt[:PROMPT_LIMIT] + "…（已截斷）"
            parts.append("## 使用者\n\n" + prompt)
            parts.append("## 回覆\n\n" + "\n\n".join(replies))
        else:
            parts.append("\n\n".join(replies))
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write("\n\n".join(parts))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--turns", type=int, default=1)
    a = parser.parse_args()

    # 標題可能含主控台編碼印不出的字元，印不出的改成替代字元，不讓整支腳本中斷
    sys.stdout.reconfigure(errors="replace")

    def report(status, **fields):
        print(json.dumps({"status": status, **fields}, ensure_ascii=False))

    try:
        info = hc_get(a.target)
    except Exception as e:
        return report("error", message=str(e))

    agent_status = info.get("status") or {}
    kind, status = AGENT_KINDS.get(agent_status.get("app")), agent_status.get("state")
    base = {"agent": kind, "terminal": info.get("address")}
    if kind is None:
        return report("unsupported", **base)
    if status in ("working", "blocked"):
        return report("busy", agent_status=status, **base)

    if kind == "claude":
        session_id = claude_session_id(info)
        base["session_id"] = session_id
        if not session_id:
            return report("no_session", **base)
        path = claude_transcript(session_id)
    else:
        rollouts = codex_rollouts(info)
        if len(rollouts) != 1:
            return report("no_session", candidates=len(rollouts), **base)
        path, base["session_id"] = rollouts[0]
    if not path:
        return report("not_found", **base)

    # 終端機標題開頭可能帶 agent 的狀態符號
    terminal_title = re.sub(r"^[^\w/\\]+", "", info.get("title") or "")
    if kind == "claude" and terminal_title not in GENERIC_TITLES:
        # 對話換過 session 時，比對標題可以避免讀到上一段對話
        transcript_title = claude_title(path)
        if transcript_title and transcript_title != terminal_title:
            return report("stale", terminal_title=terminal_title, transcript_title=transcript_title, transcript=path, **base)
    try:
        turns, pending = claude_turns(path) if kind == "claude" else codex_turns(path)
    except Exception as e:
        return report("error", message=str(e), transcript=path, **base)
    if not turns:
        return report("not_found", transcript=path, **base)

    picked = turns[-max(a.turns, 1):]
    write_turns(a.out, picked, include_prompts=a.turns > 1)
    report("ok", out=a.out, turns=len(picked), running=pending, chars=os.path.getsize(a.out), transcript=path, **base)


if __name__ == "__main__":
    sys.exit(main())
