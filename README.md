# tony-skills

套件版本：`v0.10.0`
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
| `herdr-dual-review` | 用 Herdr 並行執行 Claude 與 Codex 原生 code review，交叉質詢單方發現後彙整為 `REVIEW.md` |
| `herdr-agent-skill` | 經 Herdr 把指定的 skill 或 slash 指令（含 `/compact`）送進 Codex 或 Claude 執行，避開補全選單與 Git Bash 改寫指令 |

### herdr-dual-review

明確呼叫並指定目標分支，例如 `目標分支：dev`；可另外指定兩邊的模型與 effort。主 agent 可以是 Claude 或 Codex。

1. Claude（`/code-review high`）與 Codex（`codex review`）同時審查，只讀不寫。主 agent 是 Claude 時，Claude 審查直接在背景 fork 執行，只有 Codex 透過 Herdr 開；主 agent 是 Codex 時，兩邊都透過 Herdr 開。
2. 只有一方抓到的 P0–P2，交給另一方質詢一輪。
3. 依 Codex review 的 P0–P3 等級由上而下排序，每條標註本分支引入或既有問題，以及沿用同樣寫法的其他位置，寫入系統 temp 的 `dual-review/` 並回報路徑。
4. 關閉 Codex 的 pane，保留 Claude 審查者，方便逐條討論時接著問。

### herdr-agent-skill

agent 要透過 Herdr 叫 Codex 或 Claude 執行 skill 或 slash 指令時自動觸發，例如「用 herdr 交給 Codex 跑 `/mattpocock-skills:code-review ...`」或「幫右邊的 Claude agent `/compact`」。要跑什麼、帶什麼參數由呼叫端決定，本 skill 只負責送達。

1. 沿用既有的 agent pane，沒有就開一個；對方忙碌時先等它閒置。
2. 從 PowerShell 送，或在 Git Bash 加 `MSYS_NO_PATHCONV=1`，避免 `/compact` 被改寫成 `C:/Program Files/Git/compact`。
3. 照原樣執行指定的 skill，不換成內建的同類功能；Codex 用 `$skill`、Claude 用 `/skill`，同名候選對不上就問使用者。
4. Codex 分步輸入（先送名稱、確認選單選中後插入、補參數、確認整行才送出）；Claude 整行送出、確認輸入框後按 Enter。
5. 確認 agent 照流程進行後等待完成，回報結果並保留 pane。選單與確認畫面一律交給使用者操作。

## 前置需求

Herdr、Claude Code CLI、Codex CLI、Python 3。主 agent 必須在 Herdr 的 pane 裡執行。
