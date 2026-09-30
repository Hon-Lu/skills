"""阻塞等待審查者完成，期間不輸出任何東西；結束時只印一行 JSON。

完成訊號看檔案，不看 herdr 的 idle 狀態：Claude 的 /code-review 會把審查丟到背景，
主對話可能先變 idle，審查其實還沒結束。

用法：
  python wait_for.py --marker-file <claude 輸出檔> --exists <codex done.json> \
      --agent <claude 審查者名稱> [--timeout-sec 540] [--poll-sec 10]

status：done 全部就緒；blocked 有審查者停在授權或提問畫面；
        missing 審查者已不在；timeout 逾時但仍在進行，可再呼叫一次。
"""
import argparse
import json
import os
import subprocess
import time

MARKER = "<!-- REVIEW-END -->"


def marker_ready(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return MARKER in f.read()
    except OSError:
        return False


def find_key(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = find_key(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_key(v, key)
            if r is not None:
                return r
    return None


def agent_status(name):
    r = subprocess.run(["herdr", "agent", "get", name], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return "missing"
    try:
        return find_key(json.loads(r.stdout), "agent_status") or "unknown"
    except ValueError:
        return "unknown"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--marker-file", action="append", default=[])
    p.add_argument("--exists", action="append", default=[])
    p.add_argument("--agent", action="append", default=[])
    p.add_argument("--timeout-sec", type=int, default=540)
    p.add_argument("--poll-sec", type=int, default=10)
    a = p.parse_args()

    deadline = time.time() + a.timeout_sec
    while True:
        waiting = [f for f in a.marker_file if not marker_ready(f)]
        waiting += [f for f in a.exists if not os.path.exists(f)]
        if not waiting:
            print(json.dumps({"status": "done"}, ensure_ascii=False))
            return

        statuses = {n: agent_status(n) for n in a.agent}
        blocked = [n for n, s in statuses.items() if s == "blocked"]
        missing = [n for n, s in statuses.items() if s == "missing"]
        if blocked or missing:
            status = "blocked" if blocked else "missing"
            print(json.dumps({"status": status, "agents": blocked or missing, "waiting": waiting}, ensure_ascii=False))
            return

        if time.time() >= deadline:
            print(json.dumps({"status": "timeout", "waiting": waiting}, ensure_ascii=False))
            return
        time.sleep(a.poll_sec)


if __name__ == "__main__":
    main()
