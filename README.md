# tony-skills

套件版本：`v0.3.0`
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
| `mr-review` | 合併前的 code review。開場主動問走「標準」還是「Matt Workflow」：前者由你給目標分支與變更目的；後者只給目標分支，規格與 ticket 從 `.ai/.scratch/<分支名>/` 取得。所有候選一律通過證據門檻後才輸出 P0–P3 findings。 |

### mr-review

完整調用 Matt 的 `code-review` 取得 Standards 與 Spec 兩軸候選，再套上三層本 skill 自己的規則：

| 層 | 內容 |
| --- | --- |
| 審查範圍 | 審什麼、可以追查到多遠、diff 外的問題什麼條件下才算 |
| 規則 | `references/review-rules.md`：正確性、資安（OWASP）、資料存取與交易、API 向後相容性、程式碼品質，第 6 節為技術別補充 |
| 門檻 | 五關證據門檻與明確排除，決定候選夠不夠格被寫進 `REVIEW.md` |

三層的關係是：**規則負責找出候選，門檻負責刷掉候選**。任何來源的候選都要走完五關——Matt 兩軸報過的、規則命中的、自行追查發現的，一律不因來源而免驗。

規則檔第 1 至 5 節與技術無關，第 6 節（目前為 .NET / C#）只在專案使用該技術時適用；要支援其他技術，在第 6 節並列子節即可，前五節不用動。

## 前置需求

| 相依 | 用途 | 缺少時 |
| --- | --- | --- |
| [Matt Pocock 的 skills](https://github.com/mattpocock/skills) | `mr-review` 完整調用其 `code-review` 取得兩軸候選 | 無法運作 |
| `.ai/.scratch/<分支名>/` 下的規格與 ticket | `mr-review` 模式 B 的審查背景來源 | 模式 B 不可用，改走模式 A |
