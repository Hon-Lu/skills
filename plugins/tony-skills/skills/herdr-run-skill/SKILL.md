---
name: herdr-run-skill
description: 經 Herdr 讓 Codex 或 Claude agent 執行指定的 skill 或 slash 指令。agent 要透過 Herdr 把 skill 或 slash 指令交給 Codex 或 Claude 執行時使用。需 HERDR_ENV=1。
---

# Herdr 交 agent 執行 skill 或 slash 指令

把呼叫端指定的 skill 或 slash 指令送進 Codex 或 Claude 執行。要跑哪個 skill、帶什麼參數由呼叫端決定，本 skill 只負責正確送達。Herdr 的一般用法（開 pane、讀畫面、等待）看原生 `herdr` skill；讀對方的回覆看 `herdr-read-reply`。

## 前置

- `HERDR_ENV` 不是 `1` 就告知使用者並停止。
- 沿用既有的 agent pane；沒有就照原生 `herdr` skill 開一個同層 pane，再啟動 agent：
  - Codex：`herdr agent start <name> --kind codex --pane <pane> -- -c check_for_update_on_startup=false`，關掉啟動時的更新檢查。
  - Claude：`herdr agent start <name> --kind claude --pane <pane>`。
- 送 Claude 前，對方若是 `working` 就先 `herdr agent wait <name>`。

## 剛啟動的 agent：確認可以接收輸入

**只在本 skill 剛 `agent start` 的 agent 上做。** 沿用既有的 agent 時，它早已初始化完成，略過這一節，直接照下面兩節送出。

agent 畫面出現後還要初始化一陣子，Codex 實測可能超過一分鐘；畫面看起來就緒，送進去的字仍可能被吃掉。送第一個指令前，先只送觸發字元，等候選清單出現：

```powershell
python "SKILL_DIR/scripts/wait_ready.py" --target <agent 名稱或 pane id> --trigger '<觸發字元>'
```

- 觸發字元：`$`（Codex 的 skill）或 `/`（Claude，以及 Codex 的 slash 指令）。
- 每輪送一次觸發字元，最多等 10 秒；沒出現清單就 `ctrl+u` 清掉再送下一輪，累計 120 秒就停止。呼叫時把 shell 工具的 timeout 設到 150 秒以上。
- 從 Git Bash 呼叫時同樣要加 `MSYS_NO_PATHCONV=1`，否則 `/` 會被改寫成路徑。

stdout 只印一行 JSON，依 `status` 處理：

- `ready`：初始化完成，觸發字元留在輸入框裡。接著照下面兩節送出名稱，不要清掉重打。
- `blocked`：對方停在提示、選擇或授權畫面，腳本沒有送任何字。讀 `screen` 指向的畫面存檔，照「pane 操作界線」處理。
- `timeout`：120 秒仍沒出現清單，輸入框已清空。不要再重試，讀 `screen` 指向的畫面存檔，轉告使用者。
- `error`：herdr 指令失敗，把 `message` 轉告使用者。

## 從哪個 shell 送

Git Bash 會把開頭是 `/` 的參數當成路徑改寫，`/compact` 送到對方變成 `C:/Program Files/Git/compact`，對方當成一般訊息收下。

- 用 PowerShell 送；`$` 開頭的字串用單引號，雙引號會被展開成變數。
- 只能用 Git Bash 時，在每個 `herdr` 指令前加 `MSYS_NO_PATHCONV=1`。

## 指令轉換

- **照指定的 skill 執行，不換成 agent 內建的同類功能**（例如要求跑某個 code-review skill，不改跑 `codex review`）。
- Codex 的 skill 一律用 `$` 觸發：呼叫端給的 `/xxx` 若是 skill 而不是 Codex 的 slash 指令，改成 `$xxx`。
- Claude 的 skill 與 slash 指令都用 `/` 觸發，plugin 內的 skill 寫成 `/<plugin>:<skill>`：呼叫端給的 `$xxx` 改成 `/xxx`。
- 指令只給短名、或選單有多個同名候選時，選與完整名稱相符的那一個；對不上就停下來問使用者，不要猜。

## 送到 Codex：分步輸入

不能用 `herdr agent prompt` 一次送整行：`$`、`/` 會叫出 Codex 的補全選單，開頭被選單吃掉，Codex 只收到後面的參數，當成一般需求開始動工。

1. 送出觸發字元與名稱：
   - 沿用既有的 agent：`herdr pane send-text <pane> '$<skill 名稱>'`（slash 指令則為 `/<指令>`）。
   - 剛啟動的 agent：`wait_ready.py` 回 `ready` 後觸發字元已在輸入框，只送 `herdr pane send-text <pane> '<skill 名稱>'`。
2. `herdr agent read <name> --source visible`：確認選單選中的是目標（畫面出現該 skill 與 `enter insert`）。
3. `herdr pane send-keys <pane> enter`：插入選項，不會送出。
4. `herdr pane send-text <pane> ' <參數>'`
5. 再讀一次畫面，確認整行無誤。
6. `herdr pane send-keys <pane> enter`：送出。

## 送到 Claude：整行送出

不能用 `herdr agent prompt`：Claude 會把整段當一般訊息收下，`/` 不會觸發 skill 或指令。Claude 的選單不會吃掉已打完的名稱，用 `pane send-text` 整行一次送。

1. 送出整行：
   - 沿用既有的 agent：`herdr pane send-text <pane> '/<指令> <參數>'`。
   - 剛啟動的 agent：`wait_ready.py` 回 `ready` 後 `/` 已在輸入框，只送 `herdr pane send-text <pane> '<指令> <參數>'`。
2. `herdr agent read <name> --source visible`：確認輸入框是 `❯ /<指令> <參數>`。輸入框裡的灰字是 Claude 的建議文字，不是已輸入的內容。
3. `herdr pane send-keys <pane> enter`：送出。

## 送出之後

- 讀回應，確認 Codex 或 Claude 有照該 skill 的流程進行，再 `herdr agent wait <name>` 等待。看出誤解就立刻 `herdr agent send-keys <name> esc` 中斷並回報使用者。
- 等待期間不要反覆讀畫面看進度。
- 完成後讀結果回報使用者，並附上 pane ID；pane 保留不關，方便接著問。回覆長、要原文時看 `herdr-read-reply`。

## pane 操作界線

Codex 或 Claude 停在選單、授權或提問畫面時，只把畫面內容轉告使用者，由使用者自己到 pane 回應，不代按。
