# tony-skills

套件版本：`v0.19.1`
對應 Herdr App：`herdr-app 0.1.16`、`hc 0.1.22`
安裝教程：[INSTALL.md](./INSTALL.md)
<!-- 版本對齊 plugins/tony-skills/.claude-plugin/plugin.json 與 .codex-plugin/plugin.json，發版時三處一併更新 -->

---

## 介紹

> [!NOTE]
> 目前 Plugin 僅支持 **Claude Code** 與 **Codex** 安裝

Tony 的 Skills。

## 目前收錄的 skill

| Skill | 用途 |
| --- | --- |
| `herdr-dual-review` | 用 Herdr App 並行執行 Claude 與 Codex 原生 code review，交叉質詢單方發現，查證每條後彙整為附處理建議的 `REVIEW.md` |
| `herdr-run-skill` | 經 Herdr App 把指定的 skill 或 slash 指令送進 Codex 或 Claude 執行，新開時帶在啟動參數，既有的 agent 不帶 `<hc>` 標記送出，兩者都附上回報要求，並避開 Git Bash 改寫指令 |
| `herdr-read-reply` | 經 Herdr App 讀取另一個 agent 的回覆：依要看的東西選讀畫面或讀對話紀錄原文 |

## Herdr 協作規則（Claude Code）

Claude Code 在 Herdr App 的終端機啟動時（`HC_TERMINAL_ID` 有值），plugin 的 SessionStart hook 會把 `plugins/tony-skills/hooks-handlers/herdr-rules.md` 帶入 context：轉述給其他 agent 時表明身分、不代替使用者確認、一次性代工改用 sub-agent，開 Herdr agent 時用 `hc run --bg` 留在背景，使用者要求顯示時才放進自己所在的 tab（`keep_beside.py`），不開新 tab；照 hc 的標準流程，派工時要求對方完成、停下或卡住時用 `hc send` 回報，收到要求就照做，需要結果才 `hc wait`。新開 session、resume、`/clear` 與 context 壓縮後都會重新帶入；不在 Herdr App 內不輸出。修改規則檔後，已開著的 session 要等下一次觸發才會讀到新版。Codex 不支援，需要 `python` 在 PATH 上。

### herdr-dual-review

明確呼叫並指定目標分支與審查對象，例如 `目標分支：dev，審查對象：別人的 MR`；可另外指定需求來源（ticket、規格或 issue）與兩邊的模型與 effort。主 agent 可以是 Claude 或 Codex。

1. Claude（`/code-review high`）與 Codex（`codex review`）同時審查，只讀不寫。不論主 agent 是 Claude 或 Codex，兩邊都透過 `hc` 在背景開，各自是全新的 context，Claude 審查者也能指定模型與 effort。
2. 只有一方抓到的 P0–P2，交給另一方質詢一輪。
3. 主 agent 對照程式碼與需求來源查證每一條（含 P3），回答白話問題、是否這次造成、會不會發生、後果與修法。原條目與等級不動。
4. 依審查對象給出建議，判斷依據不看等級：自己的分支是修／不修／你判斷；別人的 MR 是阻擋／建議／待查證／不提，並另外產出可貼上 MR 的 `MR-COMMENT.md`。
5. 依 Codex review 的 P0–P3 等級由上而下排序，最上方放建議摘要與總表，每條標註本分支引入或既有問題，以及沿用同樣寫法的其他位置，寫入系統 temp 的 `dual-review/` 並回報路徑。使用者可以直接回「修 1、3」。
6. 移除 Codex 已結束的終端機，保留 Claude 審查者，方便逐條討論時接著問。

本地目標分支落後 `origin` 時自動改用 `origin/<分支>` 計算範圍（不會 fetch）。

### herdr-run-skill

agent 要透過 Herdr 叫 Codex 或 Claude 執行 skill 或 slash 指令時自動觸發，例如「用 herdr 交給 Codex 跑 `/mattpocock-skills:code-review ...`」或「叫右邊的 Claude agent 跑 `/simplify`」。要跑什麼、帶什麼參數由呼叫端決定，本 skill 只負責送達。

1. 沿用既有的 agent，沒有就用 `hc run --bg` 開，第一個指令直接帶在啟動參數，預設留在背景；使用者要求顯示時才用 `keep_beside.py` 放進呼叫端所在的 tab，不會開到使用者正在看的別的 tab。Codex 以 `--no-daemon -c check_for_update_on_startup=false -c features.hooks=false` 啟動，不跳 hook 信任畫面，也不執行 hook。
2. 既有的 agent 用 `hc send`：要觸發 skill 或 slash 指令時，只在這次呼叫清掉 `HC_TERMINAL_ID`，不帶 `<hc>` 來源標記；一般對話一律保留標記。
3. 從 PowerShell 送，或在 Git Bash 加 `MSYS_NO_PATHCONV=1`，避免 `/compact` 被改寫成 `C:/Program Files/Git/compact`。
4. 照原樣執行指定的 skill，不換成內建的同類功能；Codex 用 `$skill`、Claude 用 `/skill`，名稱對不上就問使用者。
5. 觸發 skill 的訊息沒有 `<hc>` 標記的 `reach`，所以在參數後附上 hc 標準的回報要求，對方停下時會用 `hc send` 回報。呼叫端要拿到結果才能往下時才用 `hc wait` 等待，否則不等；回報結果並保留 agent。選單與確認畫面一律交給使用者操作。

### herdr-read-reply

agent 要看另一個 agent 的回覆時自動觸發，例如「看一下右邊的 agent 回了什麼」。

1. 依要看的東西選來源：狀態列、選單、短回覆讀畫面；長報告、要逐字引用或前幾回合的問答，用 `read_reply.py` 讀 Claude 或 Codex 的對話紀錄原文。
2. `read_reply.py` 把回覆寫成 UTF-8 檔，只回一行 JSON 狀態；讀不到紀錄時改讀畫面。

## 前置需求

Herdr App（含 `hc`）、Claude Code CLI、Codex CLI、Python 3。主 agent 必須在 Herdr App 的終端機裡執行。
