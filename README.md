# tony-skills

套件版本：`v0.12.0`
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
| `herdr-dual-review` | 用 Herdr 並行執行 Claude 與 Codex 原生 code review，交叉質詢單方發現，查證每條後彙整為附處理建議的 `REVIEW.md` |
| `herdr-run-skill` | 經 Herdr 把指定的 skill 或 slash 指令送進 Codex 或 Claude 執行，避開補全選單與 Git Bash 改寫指令 |
| `herdr-read-reply` | 經 Herdr 讀取另一個 pane 的內容：依要看的東西選讀畫面或讀 agent 的對話紀錄原文，並附 PowerShell 5.1 另存終端機輸出的寫法 |

### herdr-dual-review

明確呼叫並指定目標分支與審查對象，例如 `目標分支：dev，審查對象：別人的 MR`；可另外指定需求來源（ticket、規格或 issue）與兩邊的模型與 effort。主 agent 可以是 Claude 或 Codex。

1. Claude（`/code-review high`）與 Codex（`codex review`）同時審查，只讀不寫。主 agent 是 Claude 時，Claude 審查直接在背景 fork 執行，只有 Codex 透過 Herdr 開；主 agent 是 Codex 時，兩邊都透過 Herdr 開。
2. 只有一方抓到的 P0–P2，交給另一方質詢一輪。
3. 主 agent 對照程式碼與需求來源查證每一條（含 P3），回答白話問題、是否這次造成、會不會發生、後果與修法。原條目與等級不動。
4. 依審查對象給出建議，判斷依據不看等級：自己的分支是修／不修／你判斷；別人的 MR 是阻擋／建議／待查證／不提，並另外產出可貼上 MR 的 `MR-COMMENT.md`。
5. 依 Codex review 的 P0–P3 等級由上而下排序，最上方放建議摘要與總表，每條標註本分支引入或既有問題，以及沿用同樣寫法的其他位置，寫入系統 temp 的 `dual-review/` 並回報路徑。使用者可以直接回「修 1、3」。
6. 關閉 Codex 的 pane，保留 Claude 審查者，方便逐條討論時接著問。

本地目標分支落後 `origin` 時自動改用 `origin/<分支>` 計算範圍（不會 fetch）。

### herdr-run-skill

agent 要透過 Herdr 叫 Codex 或 Claude 執行 skill 或 slash 指令時自動觸發，例如「用 herdr 交給 Codex 跑 `/mattpocock-skills:code-review ...`」或「叫右邊的 Claude agent 跑 `/simplify`」。要跑什麼、帶什麼參數由呼叫端決定，本 skill 只負責送達。

1. 沿用既有的 agent pane，沒有就開一個（Codex 以 `-c check_for_update_on_startup=false` 啟動）；對方忙碌時先等它閒置。
2. 剛啟動的 agent 送第一個指令前，由 `wait_ready.py` 只輸入 `$` 或 `/`，候選清單出現才代表初始化完成；每輪最多等 10 秒，沒出現就 `ctrl+u` 清掉再送，累計 120 秒停止並轉告使用者。
3. 從 PowerShell 送，或在 Git Bash 加 `MSYS_NO_PATHCONV=1`，避免 `/compact` 被改寫成 `C:/Program Files/Git/compact`。
4. 照原樣執行指定的 skill，不換成內建的同類功能；Codex 用 `$skill`、Claude 用 `/skill`，同名候選對不上就問使用者。
5. Codex 分步輸入（接在觸發字元後送名稱、確認選單選中後插入、補參數、確認整行才送出）；Claude 接在 `/` 後送出其餘整行、確認輸入框後按 Enter。
6. 確認 agent 照流程進行後等待完成，回報結果並保留 pane。選單與確認畫面一律交給使用者操作。

### herdr-read-reply

agent 要看另一個 pane 的內容時自動觸發，例如「看一下右邊的 agent 回了什麼」，或要在 pane 跑指令並取得結果。

1. 依要看的東西選來源：狀態列、選單、短回覆讀畫面；長報告、要逐字引用或前幾回合的問答，用 `read_reply.py` 讀 Claude 或 Codex 的對話紀錄原文。
2. `read_reply.py` 把回覆寫成 UTF-8 檔，只回一行 JSON 狀態；讀不到紀錄時改讀畫面。
3. 終端機照原生 `herdr` 用法；輸出長或要確定結束代碼時，附 PowerShell 5.1 實測可用的另存寫法與常見坑。

## 前置需求

Herdr、Claude Code CLI、Codex CLI、Python 3。主 agent 必須在 Herdr 的 pane 裡執行。
