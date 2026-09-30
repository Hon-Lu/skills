# 雙審 Code Review：{branch}

- **範圍**：`{branch}` 相對 `{base}`（merge-base `{merge_base}`，{commits} 個 commit，{files_changed} 個檔案）
- **Claude**：`/code-review high {base}...HEAD`，模型 {claude_model}，effort {claude_effort}
- **Codex**：`codex review --base {base}`，模型 {codex_model}，effort {codex_effort}
- **原始結果**：`{run_dir}`

| 等級 | 數量 |
| --- | --- |
| P1 | {n_p1} |
| P2 | {n_p2} |
| P3 | {n_p3} |

- [P1] {一句話講問題}
  - **發現者**：Claude、Codex
  - **原始等級**：Claude 高（補標）／Codex P1
  - **位置**：`{file}:{line}`
  - **問題**：{具體行為}
  - **觸發情境**：{什麼輸入或狀態下會出錯}

- [P1] {一句話講問題}
  - **發現者**：Codex
  - **原始等級**：Codex P1
  - **位置**：`{file}:{line}`
  - **問題**：{具體行為}
  - **觸發情境**：{什麼輸入或狀態下會出錯}
  - **質詢**：⚠ Claude 回覆不成立 — `{file}:{line}` {對方的理由}

- [P2] {一句話講問題}
  - **發現者**：Claude
  - **原始等級**：Claude 中
  - **位置**：`{file}:{line}`
  - **問題**：{具體行為}
  - **觸發情境**：{什麼輸入或狀態下會出錯}
  - **質詢**：Codex 回覆成立 — `{file}:{line}` {一句證據}

- [P3] {一句話講問題}
  - **發現者**：Claude
  - **原始等級**：Claude 低
  - **位置**：`{file}:{line}`
  - **問題**：{具體行為}
