# tony-skills

套件版本：`v0.6.0`
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

### herdr-dual-review

明確呼叫並指定目標分支，例如 `目標分支：dev`；可另外指定兩邊的模型與 effort。主 agent 可以是 Claude 或 Codex。

1. Claude（`/code-review high`）與 Codex（`codex review`）同時審查，只讀不寫。
2. 只有一方抓到的 P1、P2，交給另一方質詢一輪。
3. 依審查者原本的等級排序成 P1–P3，寫入系統 temp 的 `dual-review/` 並回報路徑。

## 前置需求

Herdr、Claude Code CLI、Codex CLI、Python 3。主 agent 必須在 Herdr 的 pane 裡執行。
