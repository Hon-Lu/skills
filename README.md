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
| `mr-review` | 合併前的 code review。開場主動問走「標準」還是「Matt Workflow」：前者由你給目標分支與變更目的；後者只給目標分支，規格與 ticket 從 `.ai/.scratch/<分支名>/` 取得。三軸子代理找候選，主流程逐條以證據門檻驗證後才輸出 P0–P3 findings。 |

### mr-review

獨立運作，不依賴其他 code review skill。流程分成「找」與「驗」兩段：

| 段 | 由誰做 | 內容 |
| --- | --- | --- |
| 找 | Standards 軸子代理 | `references/standards-axis.md`：repo 規範、正確性與回歸、實質效能、API 向後相容性、程式碼品質 |
| 找 | Risk 軸子代理 | `references/risk-axis.md`：資安與權限、後端信任邊界、資料一致性與交易、併發 |
| 找 | Spec 軸子代理 | `references/spec-axis.md`：需求缺漏、實作與需求不符、需求層級的權限與限制、範圍外變更、測試缺口 |
| 驗 | 主流程 | 回到程式碼逐條重新查證三軸候選，合併同根因、走完五關證據門檻與明確排除，判定確認程度與 P0–P3 |

三軸以平行子代理執行、互不共用 context，避免「寫法合規但做錯需求」「照需求做但引入越權或超扣」「邏輯正確但同時操作下資料錯亂」互相遮蔽。**子代理負責找出候選，主流程負責刷掉候選**：任何來源的候選都要走完五關，不因來源而免驗。

Standards 與 Risk 軸的最後一節是技術別補充（目前為 .NET / C#），只在專案使用該技術時適用；要支援其他技術，在該節並列子節即可，前面各節不用動。

## 前置需求

| 相依 | 用途 | 缺少時 |
| --- | --- | --- |
| `.ai/.scratch/<分支名>/` 下的規格與 ticket | `mr-review` 模式 B 的審查背景來源 | 模式 B 不可用，改走模式 A |
