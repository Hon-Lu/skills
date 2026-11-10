---
name: herdr-run-skill
description: 經 Herdr App 讓 Codex 或 Claude agent 執行指定的 skill 或 slash 指令。agent 要透過 Herdr 把 skill 或 slash 指令交給 Codex 或 Claude 執行時使用。需在 Herdr App 的終端機內（HC_TERMINAL_ID 有值）。
---

# Herdr App 交 agent 執行 skill 或 slash 指令

把呼叫端指定的 skill 或 slash 指令送進 Codex 或 Claude 執行。要跑哪個 skill、帶什麼參數由呼叫端決定，本 skill 只負責正確送達。Herdr App 的一般用法看 `hc --skill`（終端機與 agent）和 `herdr-app --skill`（視窗）。舊版 `herdr` CLI 的指令在 Herdr App 不適用。

本 skill 對應 herdr-app 0.1.14、hc 0.1.19。版本更新後行為不符時，以 `hc --skill`、`herdr-app --skill` 為準。

以下 `SKILL_DIR` 指這份 SKILL.md 所在目錄。

## 前置

- `HC_TERMINAL_ID` 沒有值就告知使用者並停止。
- 用 `hc ls` 找既有的 agent。有就沿用，照「沿用既有的 agent」送出；沒有才新開。

## 新開 agent：第一個指令直接帶在啟動參數

用 `hc run` 啟動時把 skill 當第一個 prompt 帶入，不必等就緒，也不會被補全選單吃掉。

先取得呼叫端所在的位置，讓 agent 開在同一個 tab：

```bash
hc get "$HC_TERMINAL_ID"    # labels 裡的 herdr.space、herdr.tab；PowerShell 用 $env:HC_TERMINAL_ID
```

Codex：

```bash
hc run --bg --json --name <名稱> --outlive-parent --cwd "<目錄>" --label herdr.space=<space> --label herdr.tab=<tab> codex --no-daemon -c check_for_update_on_startup=false -c features.hooks=false '$<skill> <參數>'
```

Claude：

```bash
hc run --bg --json --name <名稱> --outlive-parent --cwd "<目錄>" --label herdr.space=<space> --label herdr.tab=<tab> claude '/<plugin>:<skill> <參數>'
```

- `--no-daemon`：Codex 必加，否則它的指令會跑在 hc 之外。
- `-c features.hooks=false`：這個 Codex 不執行任何 hook，也不會跳 hook 信任畫面。不要改用 `--dangerously-bypass-hook-trust`，那會執行未經信任的 hook。
- `--outlive-parent`：呼叫端結束後 agent 仍保留，方便接著問。
- 不要用 `herdr-app do terminal.open` 開 agent：它沒有指定位置的參數，會開到使用者目前焦點所在的 tab。
- 名稱已被占用時換一個，例如加 `-2`，後續指令都用同一個名稱。
- 啟動參數不經過 `hc send`，對方收到的內容沒有 `<hc>` 來源標記。代使用者轉述時，要在參數裡說明來源。

## 沿用既有的 agent

從 agent 用 `hc send` 送出的內容，對方收到時會包成 `<hc from="t9">…</hc>`。這個來源標記對一般對話有用，但開頭不再是 `/`，slash 指令與 skill 不會觸發；自然語句請對方調用也不行，設了 `disable-model-invocation` 的 skill 會拒絕。

所以**要觸發 skill 或 slash 指令時一律不帶標記，其他對話一律保留標記**，不依情況判定。`hc send` 沒有對應選項，做法是只在這一次呼叫清掉 `HC_TERMINAL_ID`：

```bash
env -u HC_TERMINAL_ID MSYS_NO_PATHCONV=1 hc send --wait <名稱> '/<plugin>:<skill> <參數>'    # Claude
env -u HC_TERMINAL_ID hc send <名稱> '$<skill> <參數>'                                      # Codex：不加 --wait，見「送出之後」
```

```powershell
$sender = $env:HC_TERMINAL_ID; Remove-Item Env:HC_TERMINAL_ID; hc send --wait <名稱> '/<plugin>:<skill> <參數>'; $env:HC_TERMINAL_ID = $sender
```

- 內建 slash 指令（例如 `/compact`）用同樣的寫法。
- 這是實測 hc 0.1.19 的行為，文件沒有保證。送出後用 `hc read --lines 0 <名稱>` 確認對方有觸發；出現 `<hc from=` 或對方把它當一般訊息，就停下來轉告使用者，改請使用者親自輸入。
- 少了標記，對方看不出訊息來自 agent。代使用者轉述時，要在參數裡說明來源。
- `hc get` 的 `status` 是 `null` 時，`hc send` 不會擋下：對方若停在信任或選單畫面，Enter 會直接回答它（實測把 Claude 的信任畫面答成「No, exit」）。送出前先用 `hc read --lines 0 <名稱>` 確認對方停在輸入框。

## 從哪個 shell 送

- Git Bash 會把開頭是 `/` 的參數當成路徑改寫，`/compact` 送到對方會變成 `C:/Program Files/Git/compact`。在每個 `hc` 指令前加 `MSYS_NO_PATHCONV=1`。
- PowerShell 不會改寫 `/`；`$` 開頭的字串用單引號，雙引號會被展開成變數。

## 指令轉換

- **照指定的 skill 執行，不換成 agent 內建的同類功能**（例如要求跑某個 code-review skill，不改跑 `codex review`）。
- Codex 的 skill 一律用 `$` 觸發：呼叫端給的 `/xxx` 若是 skill 而不是 Codex 的 slash 指令，改成 `$xxx`。
- Claude 的 skill 與 slash 指令都用 `/` 觸發，plugin 內的 skill 寫成 `/<plugin>:<skill>`：呼叫端給的 `$xxx` 改成 `/xxx`。
- 指令只給短名、或可能有多個同名 skill 時，傳完整名稱；對不上就停下來問使用者，不要猜。

## 送出之後

等待方式依對方而定，不要反覆讀畫面看進度。

**新開的 agent 先確認有開起來**：`hc wait <名稱> --timeout 30`。回傳的 `status` 是 `null` 時，用 `hc read --lines 0 <名稱>` 看一次畫面。停在資料夾信任、選單或授權畫面，就照「操作界線」處理；正在啟動或工作，就往下等。

**Claude**：用 `hc wait <名稱>`（既有的 agent 用 `hc send --wait`）。

- `status` 有值但 `turn` 還是 `0`：第一個 prompt 還沒開始，再等一次。
- `reason` 是 `timeout` 只是到了回報時間，再等一次。
- `status` 是 `blocked`：用 `hc read --lines 0 <名稱>` 看畫面，照「操作界線」處理。

**Codex**：hc 0.1.19 實測收不到 Codex 的狀態，`status` 一直是 `null`、`turn` 一直是 `0`，`hc wait` 和 `hc send --wait` 只會等到逾時。改等它的對話紀錄：

```bash
python "SKILL_DIR/../herdr-read-reply/scripts/read_reply.py" --target <名稱> --out <暫存檔> --wait-sec 540 [--after <N>]
```

- 新開的 agent 不帶 `--after`。
- 既有的 agent 要在 `hc send` 之前，先不帶 `--wait-sec` 跑一次，記下 `completed`（`not_found` 時是 0）當作 `<N>`。
- `status` 是 `ok`：回覆已寫進 `--out`。
- `status` 是 `timeout`：用 `hc read --lines 0 <名稱>` 看畫面。還在工作就再跑一次，停在選單或授權畫面就照「操作界線」處理。

- 讀回應，確認對方有照該 skill 的流程進行。看出誤解就立刻 `hc interrupt <名稱>` 中斷並回報使用者。
- 完成後讀結果回報使用者，並附上終端機位址；agent 保留不關，方便接著問。回覆長、要原文時看 `herdr-read-reply`。

## 操作界線

Codex 或 Claude 停在選單、授權或提問畫面時，只把畫面內容轉告使用者，由使用者自己到該終端機回應，不代按，也不用 `hc send --force` 繞過。
