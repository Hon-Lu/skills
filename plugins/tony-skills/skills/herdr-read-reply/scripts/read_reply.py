"""讀取 Herdr pane 裡 Claude 或 Codex 最近完成的回合，把回覆原文寫進 UTF-8 檔案。

回覆一律寫檔不印到 stdout：Windows 主控台會把中文轉成亂碼，也避免整段回覆直接灌進呼叫端。
stdout 只印一行 JSON，status 不是 ok 時改用 herdr agent read 讀畫面。

用法：
  python read_reply.py --target <agent 名稱或 pane id> --out <輸出檔> [--turns 1]

status：
  ok           已寫入 out；running 為 true 表示紀錄裡還有未完成的回合，寫入的是它之前完成的回合
  busy         對方 working 或 blocked，先 herdr agent wait 再重跑
  no_session   Herdr 沒有記錄這個 pane 的 session id
  not_found    找不到紀錄檔，或紀錄裡沒有完成的回合
  unsupported  不是 Claude 或 Codex
  error        herdr 指令或解析失敗，message 有原因
"""
import argparse
import glob
import json
import os
import subprocess
import sys

PROMPT_LIMIT = 1500


def herdr_json(*args):
    result = subprocess.run(["herdr", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip())
    return json.loads(result.stdout)["result"]


def resolve_pane(target):
    agent = herdr_json("agent", "get", target)["agent"]
    pane = next((p for p in herdr_json("pane", "list")["panes"] if p["pane_id"] == agent["pane_id"]), None)
    session = (pane or {}).get("agent_session") or {}
    return agent, session.get("value")


def read_jsonl(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                # 對方仍在寫入時，最後一行可能還不完整
                continue


def claude_transcript(session_id):
    root = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    hits = glob.glob(os.path.join(root, "projects", "*", session_id + ".jsonl"))
    return hits[0] if hits else None


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


def codex_transcript(session_id):
    root = os.environ.get("CODEX_HOME") or os.path.join(os.path.expanduser("~"), ".codex")
    for folder in ("sessions", "archived_sessions"):
        hits = glob.glob(os.path.join(root, folder, "**", "rollout-*-" + session_id + ".jsonl"), recursive=True)
        if hits:
            return hits[0]
    return None


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

    def report(status, **fields):
        print(json.dumps({"status": status, **fields}, ensure_ascii=False))

    try:
        agent, session_id = resolve_pane(a.target)
    except Exception as e:
        return report("error", message=str(e))

    kind, status = agent.get("agent"), agent.get("agent_status")
    base = {"agent": kind, "pane_id": agent["pane_id"], "session_id": session_id}
    if kind not in ("claude", "codex"):
        return report("unsupported", **base)
    if status in ("working", "blocked"):
        return report("busy", agent_status=status, **base)
    if not session_id:
        return report("no_session", **base)

    path = claude_transcript(session_id) if kind == "claude" else codex_transcript(session_id)
    if not path:
        return report("not_found", **base)
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
