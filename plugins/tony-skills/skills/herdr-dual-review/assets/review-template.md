# 雙審 Code Review：{branch}

- **範圍**：`{branch}` 相對 `{base}`（merge-base `{merge_base}`，{commits} 個 commit，{files_changed} 個檔案）
- **Claude**：`/code-review high {base}...HEAD`，模型 {claude_model}，effort {claude_effort}
- **Codex**：`codex review --base {base}`，模型 {codex_model}，effort {codex_effort}
- **Session**：Claude `{claude_session}`／Codex `{codex_session}`
- **原始結果**：`{run_dir}`

| 等級 | 數量 |
| --- | --- |
| P0 | {n_p0} |
| P1 | {n_p1} |
| P2 | {n_p2} |
| P3 | {n_p3} |

- [P1] {一句話講問題}
  - **發現者**：Claude（CONFIRMED）、Codex
  - **位置**：`{file}:{line}`
  - **問題**：{具體行為}
  - **觸發情境**：{什麼輸入或狀態下會出錯}
  - **來源**：本分支引入
  - **同類位置**：`{file}:{line}`、`{file}:{line}`

- [P1] {一句話講問題}
  - **發現者**：Codex
  - **位置**：`{file}:{line}`
  - **問題**：{具體行為}
  - **觸發情境**：{什麼輸入或狀態下會出錯}
  - **來源**：既有問題
  - **質詢**：Claude 回覆成立 — `{file}:{line}` {一句證據}

- [P2] {一句話講問題}
  - **發現者**：Claude（PLAUSIBLE）
  - **位置**：`{file}:{line}`
  - **問題**：{具體行為}
  - **觸發情境**：{什麼輸入或狀態下會出錯}
  - **來源**：Claude：既有問題／Codex：本分支引入
  - **質詢**：⚠ Codex 回覆不成立 — `{file}:{line}` {對方的理由}

- [P3] {一句話講問題}
  - **發現者**：Codex
  - **位置**：`{file}:{line}`
  - **問題**：{具體行為}
  - **來源**：未判斷
