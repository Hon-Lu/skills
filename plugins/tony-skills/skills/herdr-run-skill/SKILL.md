---
name: herdr-run-skill
description: 經 Herdr App 讓 Codex 或 Claude agent 執行指定的 skill 或 slash 指令。agent 要透過 Herdr 把 skill 或 slash 指令交給 Codex 或 Claude 執行時使用。需在 Herdr App 的終端機內（HC_TERMINAL_ID 有值）。
---

# Herdr App 交 agent 執行 skill 或 slash 指令

把呼叫端指定的 skill 或 slash 指令送進 Codex 或 Claude 執行；跑什麼、帶什麼參數由呼叫端決定，本 skill 只負責正確送達。這裡只寫 `hc --skill` 沒有的部分，其餘照手冊，行為不符時以手冊為準。以下 `SKILL_DIR` 指這份 SKILL.md 所在目錄。

## 前置

- `HC_TERMINAL_ID` 沒有值就告知使用者並停止。
- 用 `hc ls` 找既有的 agent，有就沿用，沒有才新開。

## 指令怎麼寫

- 照指定的 skill 執行，不換成 agent 內建的同類功能（例如要求跑某個 code-review skill，不改跑 `codex review`）。
- Claude 用 `/`，plugin 內的 skill 寫成 `/<plugin>:<skill>`。Codex 的 skill 用 `$<skill>`：呼叫端給的 `/xxx` 是 skill 而不是 Codex 的 slash 指令時，改成 `$xxx`。
- 名稱不確定就傳完整名稱。Codex 的名稱可能與 Claude 不同（例如 plugin 前綴），依序查 `~/.codex/history.jsonl` 過去觸發的寫法（`grep -o '\$[^ "]*<skill>[^ "]*' ~/.codex/history.jsonl | sort | uniq -c`）、列出 `~/.codex/skills`，都查不到就問使用者。不要遞迴搜尋整個 `~/.codex`：底下的 sessions 很大，會卡住數分鐘。
- 指令後面接 `<回報要求>`：

  ```text
  （呼叫端 agent 附加）完成、停下等使用者確認或卡住時，用 hc send <呼叫端的 HC_TERMINAL_ID> 回報結果或卡點；內容長就寫進檔案、回報路徑。
  ```

  觸發 skill 的訊息沒有 `<hc>` 標記，也就沒有 `reach`，不寫的話對方停下時不會回報。skill 把整段參數當固定格式的輸入時不接，確認觸發後另用一般的 `hc send` 補送。
- 代使用者轉述時，在參數裡說明來源：這些訊息沒有 `<hc>` 標記，對方看不出來自 agent。

## 新開 agent

指令直接帶在啟動參數，不必等就緒，也不會被補全選單吃掉：

```bash
hc run --bg --json --name <名稱> --outlive-parent --cwd "<目錄>" claude '/<plugin>:<skill> <參數> <回報要求>'
hc run --bg --json --name <名稱> --outlive-parent --cwd "<目錄>" codex --no-daemon -c check_for_update_on_startup=false -c features.hooks=false '$<skill> <參數> <回報要求>'
```

- Codex 的 `-c features.hooks=false` 讓它不執行 hook，也不跳 hook 信任畫面；不要改用 `--dangerously-bypass-hook-trust`，那會執行未經信任的 hook。
- `--outlive-parent`：呼叫端結束後 agent 仍保留，方便接著問。
- 開完 `hc wait <名稱> --timeout 30`。`status` 是 `null` 時看一次畫面，停在資料夾信任或選單畫面就照「操作界線」處理。
- 使用者要求顯示時，才用 `python "SKILL_DIR/scripts/keep_beside.py" --target <名稱>` 放進呼叫端所在的 tab。直接用 `herdr-app do terminal.keep` 或 `terminal.open` 會開到使用者正在看的 tab。

## 沿用既有的 agent

`hc send` 送出的內容會包成 `<hc from="…">`，開頭不再是 `/`，skill 和 slash 指令不會觸發，自然語句請對方調用也不行。所以觸發 skill 或 slash 指令（包括 `/compact` 這類內建指令）時，只在這次呼叫清掉 `HC_TERMINAL_ID`；其他對話一律保留標記。回報要求裡的位址要在清掉之前填好。

```bash
env -u HC_TERMINAL_ID MSYS_NO_PATHCONV=1 hc send <名稱> '/<plugin>:<skill> <參數> <回報要求>'
```

```powershell
$sender = $env:HC_TERMINAL_ID; Remove-Item Env:HC_TERMINAL_ID; hc send <名稱> '/<plugin>:<skill> <參數> <回報要求>'; $env:HC_TERMINAL_ID = $sender
```

- 送出前用 `hc read --lines 0 <名稱>` 確認對方停在輸入框：`status` 是 `null` 時 `hc send` 不會擋，Enter 會直接回答信任或選單畫面（實測把 Claude 的信任畫面答成「No, exit」）。
- 送出後再看一次。出現 `<hc from=` 或對方把它當一般訊息，就停下來請使用者親自輸入。
- Git Bash 會把開頭是 `/` 的參數改寫成路徑（`/compact` 變成 `C:/Program Files/Git/compact`），每個 `hc` 前加 `MSYS_NO_PATHCONV=1`。PowerShell 不會改寫，但 `$` 開頭的字串要用單引號。

## 送出之後

- 呼叫端不需要結果就能繼續（例如對方會分段停下等使用者確認）：不等待，對方會照回報要求回報。
- 要拿到結果才能往下：新開的用 `hc wait <名稱>`，既有的送出時加 `--wait`，用法照手冊。
- 確認對方照該 skill 的流程進行，看出誤解就 `hc interrupt <名稱>` 並回報使用者。完成後回報結果並附上終端機位址，agent 保留不關。回覆長、要原文時看 `herdr-read-reply`。

## 操作界線

對方停在選單、授權或提問畫面時，只把畫面內容轉告使用者，由使用者自己到該終端機回應；不代按，也不用 `hc send --force` 繞過。
