---
name: herdr-read-reply
description: 經 Herdr 讀取另一個 pane 的內容：Claude 或 Codex agent 的回覆，或終端機指令的輸出與結束代碼。要看其他 agent 回了什麼、審查它的回報，或在 pane 跑指令並取得結果時使用。需 HERDR_ENV=1。
---

# 經 Herdr 讀取 pane 內容

讀 pane 有兩種來源，依要看的東西挑：

| 要看的 | 適合的方式 |
| --- | --- |
| 狀態列（context 用量、模型）、選單、授權或提問畫面、輸入框裡的灰字、進度 | 讀畫面：`herdr agent read` 或 `herdr pane read` |
| 短回覆、快速瞄一眼 | 讀畫面 |
| 長報告（表格、diff、程式碼區塊）、要逐字引用或轉述、前段已捲出畫面 | 讀對話紀錄：`read_reply.py` |
| 前幾回合的問答，例如某個改動是誰要求的 | 讀對話紀錄，加 `--turns N` |

畫面拿到的是渲染後的文字：表格變框線、長行被折、超過留存範圍的前段會不見。對話紀錄是對方寫出的 Markdown 原文。

`HERDR_ENV` 不是 `1` 就告知使用者並停止。

## 讀對話紀錄

```bash
python "SKILL_DIR/scripts/read_reply.py" --target <agent 名稱或 pane id> --out <輸出檔> [--turns N]
```

腳本依 Herdr 記錄的 session id 找到對方的對話紀錄，把最近完成回合的回覆寫進 `--out`（UTF-8），stdout 只印一行 JSON。`--turns N` 取最近 N 回合，並附上每回合的使用者訊息（每則截到 1500 字）。輸出檔放系統 temp 或自己的暫存目錄，再用讀檔工具讀。

`status`：

- `ok`：讀 `out`。`running` 為 `true` 表示對方還有未完成的回合，讀到的是之前完成的那一回合。
- `busy`：對方 `working` 或 `blocked`，等它停下來，或改讀畫面看它卡在哪。
- `no_session`、`not_found`、`unsupported`、`error`：這個 pane 讀不到紀錄，改讀畫面。
- `stale`：Herdr 記錄的 session 已不是 pane 目前的對話（例如對方 `/clear` 過），紀錄檔標題與 pane 標題不同，改讀畫面。

限制：

- 只適用本機的 Claude Code 與 Codex，紀錄格式不是公開契約。Codex 的 session id 要靠 Herdr 的 Codex integration 回報，沒回報就是 `no_session`。
- Claude 一回合裡穿插在工具呼叫之間的短句，會一起輸出在最終報告前面；Codex 只取最終回覆。
- 紀錄檔動輒數百 KB，不要整份讀進來；回覆也不要直接印到 Windows 主控台，中文會變成亂碼。

## 讀終端機的輸出

`herdr pane run`、`pane wait-output`、`pane read` 照原生 `herdr` skill 用。輸出長到會捲出留存範圍（約 1000 行），或要確定指令的結束代碼時，可以讓輸出同時另存檔案。

Herdr 新開的 pane 在 Windows 預設是 Windows PowerShell 5.1，實測可用的寫法：

```powershell
<指令> 2>&1 | ForEach-Object { "$_" } | Tee-Object -Variable out; $code = $LASTEXITCODE; $out | Out-File -FilePath '<log 路徑>' -Encoding utf8; "<標記> EXIT=$code"
```

```bash
herdr pane wait-output <pane> --regex "^<標記> EXIT=-?[0-9]+" --timeout <毫秒>
```

5.1 的幾個坑：

- `wait-output` 會比對畫面上已有的輸出，標記沿用舊的會直接命中上一次的結果，每次換一個（例如 `DONE-<亂數>`）。`^` 避免比對到命令列本身。
- `2>&1` 會把 stderr 包成 `NativeCommandError` 錯誤紀錄，`ForEach-Object { "$_" }` 轉回原本的訊息。
- `Tee-Object -FilePath` 寫出 UTF-16，grep 比對不到，所以改由 `Out-File -Encoding utf8` 寫檔。
- `$LASTEXITCODE` 在 pipeline 後立刻存下來，再跑其他程式就會被覆蓋。
