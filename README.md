# tony-skills

套件版本：`v0.5.0`
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
| `herdr-dual-review` | 用 Herdr 在旁邊的 pane 同時跑 Claude 與 Codex 的原生 code review，只有一方抓到的問題交給另一方質詢一輪，最後彙整成一份依 P1–P3 排序的 `REVIEW.md`。 |

### herdr-dual-review

只能明確呼叫，不會因為一般訊息自動觸發。呼叫時帶上目標分支，例如「目標分支：dev」；要指定兩邊的模型或 effort 也寫在同一句，沒寫就用各 CLI 的預設。主 agent 可以是 Claude 或 Codex。

| 步驟 | 內容 |
| --- | --- |
| 審查 | Claude 跑 `/code-review high <base>...HEAD`，Codex 跑 `codex review --base <base>`，兩邊同時進行，都只讀不寫 |
| 等待 | 主 agent 用 `scripts/wait_for.py` 阻塞等待兩邊的結果檔，期間不讀 pane 畫面 |
| 質詢 | 只有一方抓到的 P1、P2 批次送給另一方查證一輪，回覆只有成立／不成立／不確定加一行證據；Codex 會接回原本的 review session |
| 報告 | 等級照審查者原本的標示換算成 P1–P3，主 agent 不重新評級、不刪條目；質詢結果標在該條底下 |

報告與各審查者的原始結果都寫在系統 temp 的 `dual-review/<repo>-<分支>-<時間>/`，完成後主 agent 會回報 `REVIEW.md` 的路徑。

## 前置需求

| 相依 | 用途 | 缺少時 |
| --- | --- | --- |
| Herdr | 開審查者的 pane，主 agent 必須在 Herdr 的 pane 裡執行 | skill 直接停止 |
| Claude Code CLI（`claude`） | Claude 審查者 | 無法執行 |
| Codex CLI（`codex`） | Codex 審查者與質詢 | 無法執行 |
| Python 3 | `scripts/` 下的初始化、等待與 Codex 包裝腳本 | 無法執行 |
