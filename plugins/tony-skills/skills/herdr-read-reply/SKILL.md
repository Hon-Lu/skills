---
name: herdr-read-reply
description: 經 Herdr App 讀取另一個終端機的內容：Claude 或 Codex agent 的回覆，或指令的輸出與結束代碼。要看其他 agent 回了什麼、審查它的回報，或在終端機跑指令並取得結果時使用。需在 Herdr App 的終端機內（HC_TERMINAL_ID 有值）。
---

# 經 Herdr App 讀取終端機內容

讀終端機有兩種來源，依要看的東西挑：

| 要看的 | 適合的方式 |
| --- | --- |
| 狀態列（context 用量、模型）、選單、授權或提問畫面、輸入框裡的灰字、進度 | 讀畫面：`hc read --lines 0 <t>` |
| 短回覆、快速瞄一眼 | 讀畫面：`hc read --lines 100 <t>` |
| 長報告（表格、diff、程式碼區塊）、要逐字引用或轉述、前段已捲出畫面 | 讀對話紀錄：`read_reply.py` |
| 前幾回合的問答，例如某個改動是誰要求的 | 讀對話紀錄，加 `--turns N` |

`<t>` 是 `hc ls` 列出的位址（例如 `t7`）或名稱。畫面拿到的是渲染後的文字：表格變框線、長行被折、對方 `working` 時只拿得到目前畫面。對話紀錄是對方寫出的 Markdown 原文。

`HC_TERMINAL_ID` 沒有值就告知使用者並停止。

本 skill 對應 herdr-app 0.1.14、hc 0.1.19。版本更新後行為不符時，以 `hc --skill`、`herdr-app --skill` 為準。

## 讀對話紀錄

```bash
python "SKILL_DIR/scripts/read_reply.py" --target <位址或名稱> --out <輸出檔> [--turns N]
```

腳本從 `hc get` 的程序與目錄資訊找到對方的對話紀錄，把最近完成回合的回覆寫進 `--out`（UTF-8），stdout 只印一行 JSON。`--turns N` 取最近 N 回合，並附上每回合的使用者訊息（每則截到 1500 字）。輸出檔放系統 temp 或自己的暫存目錄，再用讀檔工具讀。

`status`：

- `ok`：讀 `out`。`running` 為 `true` 表示對方還有未完成的回合，讀到的是之前完成的那一回合。
- `busy`：對方 `working` 或 `blocked`，等它停下來，或改讀畫面看它卡在哪。
- `no_session`、`not_found`、`unsupported`、`error`：這個終端機讀不到紀錄，改讀畫面。
- `stale`：找到的 session 已不是終端機目前的對話（例如對方 `/clear` 過），紀錄檔標題與終端機標題不同，改讀畫面。

限制：

- 只適用本機的 Claude Code 與 Codex，紀錄格式與對應方式都不是公開契約。
- Claude 由程序 id 對應 `~/.claude/sessions/<pid>.json`。
- Codex 由目錄與啟動時間對應 rollout 檔；同一個目錄在這個終端機建立後有多個互動式 Codex 時，無法分辨，回 `no_session`。
- Claude 一回合裡穿插在工具呼叫之間的短句，會一起輸出在最終報告前面；Codex 只取最終回覆。
- 紀錄檔動輒數百 KB，不要整份讀進來；回覆也不要直接印到 Windows 主控台，中文會變成亂碼。

## 跑指令並取得結果

- 短指令：`hc exec --cwd "<目錄>" -- <指令>`，印出原始輸出並以該指令的結束代碼結束。
- 較久的指令：放到 hc 終端機，不佔住自己的 shell。

```bash
hc run --bg --no-notify --name <名稱> --cwd "<目錄>" <指令>
hc wait <名稱>              # 回傳的 exit_code 就是結束代碼；reason 是 timeout 時再等一次
hc read --lines 200 <名稱>
hc rm <名稱>                # 讀完後移除
```

等待輸出出現用 `hc wait <名稱> --output <文字>`，只比對開始等待之後才印出的內容，不要用 sleep 或反覆讀畫面。要讓使用者看到這個終端機時，加上 `--label herdr.space=<space> --label herdr.tab=<tab>`，值取自 `hc get "$HC_TERMINAL_ID"` 的 `labels`。
