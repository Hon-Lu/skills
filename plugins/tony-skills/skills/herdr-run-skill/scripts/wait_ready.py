"""在 agent 輸入框送觸發字元，等候選清單出現，用來判斷 agent 初始化完成、可以接收指令。

agent 畫面出現後還要初始化一陣子（Codex 實測可能超過一分鐘），看起來就緒時送進去的字仍可能被吃掉。
清單跳得出來，代表輸入框已能接收、skill 清單也已載入。

每輪送一次觸發字元，最多等 --round-sec 秒；沒出現清單就 ctrl+u 清掉再送下一輪。
累計 --timeout-sec 秒仍沒出現就停止，不再操作。時間以實際經過計算：初始化期間 herdr 讀畫面本身也會變慢。

用法：
  python wait_ready.py --target <agent 名稱或 pane id> --trigger '$' [--timeout-sec 120] [--round-sec 10]

stdout 只印一行 JSON。status：
  ready    清單已出現，觸發字元留在輸入框，接著送名稱即可
  blocked  agent 停在提示、選擇或授權畫面，沒有送任何字；screen 為畫面存檔的路徑
  timeout  時間到仍沒出現清單，輸入框已清空；screen 為最後畫面存檔的路徑
  error    herdr 指令失敗，message 有原因

畫面一律寫成 UTF-8 檔案，不印到 stdout：Windows 主控台印不出畫面上的部分字元。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time

# Codex 的清單底下固定有這行操作提示
CODEX_MENU = re.compile(r"enter insert")
# Claude 的清單是輸入框下方縮排的候選指令，第一列前面有 ❯
CLAUDE_MENU = re.compile(r"^\s+(❯\s+)?/[\w:.-]+\s", re.MULTILINE)


def herdr(*args):
    result = subprocess.run(["herdr", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip())
    return result.stdout


def agent_info(target):
    return json.loads(herdr("agent", "get", target))["result"]["agent"]


def screen(pane):
    return herdr("pane", "read", pane, "--source", "visible", "--lines", "40")


def save_screen(pane, text):
    path = os.path.join(tempfile.gettempdir(), "herdr-wait-ready-" + pane.replace(":", "-") + ".txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def menu_marks(kind, text):
    pattern = CODEX_MENU if kind == "codex" else CLAUDE_MENU
    return len(pattern.findall(text))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--trigger", required=True, choices=["$", "/"])
    parser.add_argument("--timeout-sec", type=float, default=120)
    parser.add_argument("--round-sec", type=float, default=10)
    a = parser.parse_args()

    def report(status, **fields):
        print(json.dumps({"status": status, **fields}, ensure_ascii=False))

    started = time.monotonic()
    elapsed = lambda: round(time.monotonic() - started, 1)
    try:
        agent = agent_info(a.target)
        pane, kind = agent["pane_id"], agent.get("agent")
        rounds = 0
        last = ""
        while time.monotonic() - started < a.timeout_sec:
            if agent_info(a.target).get("agent_status") == "blocked":
                return report("blocked", pane_id=pane, elapsed_sec=elapsed(), screen=save_screen(pane, screen(pane)))
            rounds += 1
            # 對話紀錄裡可能原本就有相同字樣，以送出前的畫面為基準，數量增加才算清單出現
            baseline = menu_marks(kind, screen(pane))
            herdr("pane", "send-text", pane, a.trigger)
            round_started = time.monotonic()
            while time.monotonic() - round_started < a.round_sec and time.monotonic() - started < a.timeout_sec:
                time.sleep(1)
                last = screen(pane)
                if menu_marks(kind, last) > baseline:
                    return report("ready", pane_id=pane, agent=kind, rounds=rounds, elapsed_sec=elapsed())
            herdr("pane", "send-keys", pane, "ctrl+u")
        report("timeout", pane_id=pane, agent=kind, rounds=rounds, elapsed_sec=elapsed(), screen=save_screen(pane, last))
    except Exception as e:
        report("error", message=str(e), elapsed_sec=elapsed())


if __name__ == "__main__":
    sys.exit(main())
