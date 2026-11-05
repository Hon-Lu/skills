"""建立雙審的執行目錄並檢查分支狀態，只輸出一行 JSON。

用法：python init_run.py --base <目標分支>
結束碼：0 可開始；2 工作區不乾淨、找不到目標分支或沒有差異。
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    # 只去掉尾端空白：porcelain 狀態碼的開頭空白有意義
    return r.returncode, r.stdout.rstrip(), r.stderr.strip()


def fail(status, **extra):
    print(json.dumps({"status": status, **extra}, ensure_ascii=False))
    sys.exit(2)


def prefer_up_to_date_base(base):
    """本地目標分支落後 origin 時改用 origin，否則分支已合併的 origin commit 會被算進審查範圍。

    不 fetch：可能跳出憑證視窗，origin 的新舊以本機上次 fetch 的結果為準。
    """
    remote = "origin/" + base
    if base.startswith("origin/") or git("rev-parse", "--verify", "--quiet", remote + "^{commit}")[0] != 0:
        return base, None

    code, counts, _ = git("rev-list", "--left-right", "--count", base + "..." + remote)
    if code != 0:
        return base, None
    ahead, behind = (int(n) for n in counts.split())
    if not behind:
        return base, None
    if ahead:
        return base, f"diverged: ahead {ahead}, behind {behind}"
    return remote, f"local_behind: {behind}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True)
    a = p.parse_args()

    code, top, _ = git("rev-parse", "--show-toplevel")
    if code != 0:
        fail("not_a_repo")

    # 未提交的變更不會進 base...HEAD，兩邊審的範圍會不一致
    _, dirty, _ = git("status", "--porcelain")
    if dirty:
        fail("dirty", files=dirty.splitlines()[:20])

    base = a.base
    if git("rev-parse", "--verify", "--quiet", base + "^{commit}")[0] != 0:
        if git("rev-parse", "--verify", "--quiet", "origin/" + base + "^{commit}")[0] == 0:
            base = "origin/" + base
        else:
            fail("base_not_found", base=a.base)

    base, base_note = prefer_up_to_date_base(base)

    _, merge_base = git("merge-base", base, "HEAD")[:2]
    _, files, _ = git("diff", "--name-only", merge_base, "HEAD")
    _, commits, _ = git("rev-list", "--count", merge_base + "..HEAD")
    if not files:
        fail("empty", base=base)

    _, branch, _ = git("rev-parse", "--abbrev-ref", "HEAD")
    _, head, _ = git("rev-parse", "--short", "HEAD")
    if branch == "HEAD":
        branch = head
    safe = re.sub(r"[^\w\-]+", "_", branch)[:40]
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = os.path.join(tempfile.gettempdir(), "dual-review", f"{os.path.basename(top)}-{safe}-{stamp}")
    os.makedirs(run_dir, exist_ok=True)

    info = {
        "status": "ok",
        "repo": top,
        "branch": branch,
        "head": head,
        "base": base,
        "merge_base": merge_base[:7],
        "commits": int(commits or 0),
        "files_changed": len(files.splitlines()),
        "run_dir": run_dir,
    }
    if base_note:
        info["base_note"] = base_note
    with open(os.path.join(run_dir, "run.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    main()
