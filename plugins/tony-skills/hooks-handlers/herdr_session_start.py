"""Herdr 管理的 pane 啟動 Claude Code 時，把 Herdr 協作規則帶入 context；不在 Herdr 內就不輸出。"""
import json
import os
import sys


def main() -> int:
    if os.environ.get("HERDR_ENV") != "1":
        return 0

    rules_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "herdr-rules.md")
    try:
        with open(rules_path, encoding="utf-8-sig") as f:
            rules = f.read()
    except OSError:
        # 規則檔遺失時不擋 session 啟動
        return 0

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": rules,
        }
    }
    # ensure_ascii 避免 Windows 主控台編碼把中文寫壞
    sys.stdout.write(json.dumps(output, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
