"""把 hc run --bg 開在背景的終端機，放進呼叫端所在的 tab（開在呼叫端旁邊，--place 選方向），再把焦點還給使用者原本看的 pane。

Herdr 的 terminal.keep 只能放在「目前焦點 pane」旁邊，沒有指定 tab 的參數；使用者正在看別的
tab 時直接 keep，pane 會開進使用者那邊。這裡先把焦點移到呼叫端，keep 之後再移回去，畫面只閃一下。

用法：
  python keep_beside.py --target <位址或名稱> [--place right|down]

stdout 只印一行 JSON：
  ok         已放好；terminal、pane、tab 是新 pane 的資訊
  no_caller  HC_TERMINAL_ID 沒有值
  not_found  找不到 target，或它已結束
  has_pane   target 已經有 pane，沒有動
  no_pane    呼叫端自己沒有 pane（例如它本身是背景子 agent），target 留在背景
  error      herdr-app 或 hc 失敗，message 有原因；焦點已盡量還原
"""
import argparse
import json
import os
import subprocess
import sys


class Failed(Exception):
    pass


def run_json(args):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        data = json.loads(r.stdout) if r.stdout.strip() else {}
    except json.JSONDecodeError:
        raise Failed(f"{args[0]} {args[1]} 輸出無法解析：{r.stdout.strip()[:200]}")
    if r.returncode != 0 or (isinstance(data, dict) and "error" in data):
        if not (isinstance(data, dict) and "error" in data):
            # hc 把錯誤以 JSON 寫到 stderr
            try:
                data = json.loads(r.stderr)
            except json.JSONDecodeError:
                data = {}
        message = data.get("error") if isinstance(data, dict) else None
        if isinstance(message, dict):
            message = message.get("message")
        raise Failed(message or r.stderr.strip() or f"{args[0]} {args[1]} 結束代碼 {r.returncode}")
    return data


def do(command, **params):
    # 參數用一個 JSON 物件傳，避開 PowerShell 與 Git Bash 的引號差異
    return run_json(["herdr-app", "do", command, json.dumps(params)])


def panes_by_terminal():
    """位址 -> (pane, tab)，只含有 pane 的終端機。"""
    out = {}
    for space in run_json(["herdr-app", "ls"]).get("spaces", []):
        for tab in space.get("tabs", []):
            for t in tab.get("terminals", []):
                if t.get("terminal") and t.get("pane"):
                    out[t["terminal"]] = (t["pane"], tab["id"])
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="hc run 回傳的位址或 --name")
    parser.add_argument("--place", choices=["right", "down"], default="right")
    args = parser.parse_args()

    def emit(status, **fields):
        sys.stdout.write(json.dumps({"status": status, **fields}, ensure_ascii=True) + "\n")
        return 0 if status in ("ok", "has_pane") else 1

    caller = os.environ.get("HC_TERMINAL_ID")
    if not caller:
        return emit("no_caller")

    try:
        # terminal.keep 只認位址，名稱要先換成位址
        try:
            info = run_json(["hc", "get", args.target, "--json"])
        except Failed as e:
            return emit("not_found", message=str(e))
        address = info.get("address")
        if info.get("state") != "live" or not address:
            return emit("not_found", message=f"{args.target} 狀態是 {info.get('state')}")

        placed = panes_by_terminal()
        if address in placed:
            pane, tab = placed[address]
            return emit("has_pane", terminal=address, pane=pane, tab=tab)
        if caller not in placed:
            return emit("no_pane", terminal=address)
        caller_tab = placed[caller][1]

        original = run_json(["herdr-app", "status"]).get("focused_pane")
        try:
            do("pane.focus", terminal=caller)
            kept = do("terminal.keep", terminal=address, place=args.place)
        finally:
            # 使用者原本就在呼叫端時，這一步會把焦點留在呼叫端，不跳到新 pane
            if original:
                try:
                    do("pane.focus", pane=original)
                except Failed:
                    pass
        if kept.get("tab") != caller_tab:
            return emit("error", terminal=address, message=f"pane 開到了 tab {kept.get('tab')}，不是呼叫端的 {caller_tab}")
        return emit("ok", terminal=address, pane=kept.get("pane"), tab=kept.get("tab"))
    except Failed as e:
        return emit("error", message=str(e))


if __name__ == "__main__":
    sys.exit(main())
