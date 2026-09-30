"""在 herdr pane 裡執行 Codex 原生 review 或質詢，結果寫檔，結束時寫 <輸出檔>.done.json。

  review：codex review --base <base>，stdout 同時顯示在 pane 並寫入 <run-dir>/codex-review.md
  ask   ：接回 review 的 session（codex exec resume）回答質詢，保留它審過的脈絡；
          沒有 session id 時退回新開一個唯讀的 codex exec

模型與 effort 沒給就不帶參數，沿用 ~/.codex/config.toml。兩種模式都強制唯讀 sandbox。
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import threading
import time


def overrides(model, effort):
    args = ["-c", 'sandbox_mode="read-only"']
    if model:
        args += ["-c", f'model="{model}"']
    if effort:
        args += ["-c", f'model_reasoning_effort="{effort}"']
    return args


def rollout_files():
    root = os.path.join(os.path.expanduser("~"), ".codex", "sessions")
    return set(glob.glob(os.path.join(root, "**", "rollout-*.jsonl"), recursive=True))


def session_id_of(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            meta = json.loads(f.readline())
        payload = meta.get("payload", {})
        # review 會拆出子 thread；resume 子 thread 實際接回的是根 session，直接記根 session
        return payload.get("session_id") or payload.get("id")
    except (OSError, ValueError):
        return None


def tee(stream, file):
    for line in stream:
        sys.stdout.write(line)
        sys.stdout.flush()
        file.write(line)


def write_done(out, **info):
    with open(out + ".done.json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False)


def review(a, codex):
    out = os.path.join(a.run_dir, "codex-review.md")
    log = os.path.join(a.run_dir, "codex-review.log")
    before = rollout_files()
    started = time.time()
    cmd = [codex, "review", "--base", a.base] + overrides(a.model, a.effort)
    print(f"[dual-review] Codex 審查中（base: {a.base}），完成前會持續顯示進度…", flush=True)
    with open(out, "w", encoding="utf-8") as fo, open(log, "w", encoding="utf-8") as fe:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        # 進度走 stderr；同步顯示在 pane 上，否則審查期間畫面一片空白
        progress = threading.Thread(target=tee, args=(proc.stderr, fe))
        progress.start()
        tee(proc.stdout, fo)
        progress.join()
        code = proc.wait()

    # review 會留下 rollout 檔；抓本次新增的那一個當質詢時要接回的 session
    new = [p for p in rollout_files() - before if os.path.getmtime(p) >= started - 5]
    new.sort(key=os.path.getmtime, reverse=True)
    sid = session_id_of(new[0]) if new else None
    write_done(out, exit_code=code, session_id=sid, output=out, log=log)
    print(f"\n[dual-review] Codex 審查結束（exit {code}），結果：{out}", flush=True)


def ask(a, codex):
    with open(a.prompt_file, encoding="utf-8") as f:
        prompt = f.read()
    if a.session:
        cmd = [codex, "exec", "resume", a.session, "-o", a.out] + overrides(a.model, a.effort) + ["-"]
    else:
        cmd = [codex, "exec", "-o", a.out] + overrides(a.model, a.effort) + ["-"]
    print("[dual-review] Codex 質詢查證中…", flush=True)
    code = subprocess.run(cmd, input=prompt, text=True, encoding="utf-8", errors="replace").returncode
    write_done(a.out, exit_code=code, session_id=a.session, output=a.out, resumed=bool(a.session))
    print(f"\n[dual-review] Codex 質詢結束（exit {code}），結果：{a.out}", flush=True)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    codex = shutil.which("codex")
    if not codex:
        print("找不到 codex CLI")
        sys.exit(1)

    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="mode", required=True)
    r = sub.add_parser("review")
    r.add_argument("--base", required=True)
    r.add_argument("--run-dir", required=True)
    q = sub.add_parser("ask")
    q.add_argument("--prompt-file", required=True)
    q.add_argument("--out", required=True)
    q.add_argument("--session")
    for s in (r, q):
        s.add_argument("--model")
        s.add_argument("--effort")
    a = p.parse_args()
    (review if a.mode == "review" else ask)(a, codex)


if __name__ == "__main__":
    main()
