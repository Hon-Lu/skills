---
name: herdr-dual-review
description: 用 Herdr 並行執行 Claude 與 Codex 原生 code review，交叉質詢單方發現後彙整為 REVIEW.md。僅在明確呼叫時使用，需指定目標分支。
disable-model-invocation: true
---

# Herdr 雙審

你是主 agent：負責開審查者、等待、轉送質詢、寫報告。你自己不做審查。

以下 `SKILL_DIR` 指這份 SKILL.md 所在目錄（通常是 `~/.agents/skills/herdr-dual-review`）。

## 0. 前置檢查與解析輸入

- 執行 `test "${HERDR_ENV:-}" = 1`（PowerShell：`$env:HERDR_ENV -eq '1'`）。不在 Herdr 裡就告知使用者並停止。
- 從使用者訊息取出：
  - **目標分支**（必填，例如「目標分支：dev」）。沒給就問。
  - **Claude 模型／effort**、**Codex 模型／effort**（選填）。使用者沒提到的就不帶參數，沿用各 CLI 的預設。- Claude 審查一律用 `/code-review high`，`high` 是 review 深度，和 session 的 effort 無關。

## 1. 建立執行目錄

```bash
python "SKILL_DIR/scripts/init_run.py" --base <目標分支>
```

輸出一行 JSON。`status` 不是 `ok` 就把原因告訴使用者並停止：`dirty` 要先 commit，`base_not_found` 找不到目標分支，`empty` 沒有差異。記下 `run_dir`、`base`（可能已補成 `origin/<分支>`）與其他欄位，填報告時會用到。

## 2. 開審查者

兩個審查者都只讀：不修改檔案、不 commit、不跑整合測試。整合測試會寫真實資料庫，兩邊同時跑會互相干擾。

```bash
herdr pane split --current --direction right --cwd "<repo>" --no-focus      # → Claude 的 pane A
herdr pane split <A> --direction down --cwd "<repo>" --no-focus             # → Codex 的 pane B
```

新 pane 的 ID 從回傳 JSON 的 `.result.pane.pane_id` 取得，不要自己推測。

兩邊要同時跑：先送 Codex，再開 Claude。下面每個指令送出後都會馬上返回，不要加 `--wait`，也不要在中間等待。兩邊都送出後，才進入第 3 步。

**Codex**（原生 review，在 pane 裡當一般指令執行，送出後就在背景跑）：

```bash
herdr pane run <B> 'python "SKILL_DIR/scripts/codex_review.py" review --base "<base>" --run-dir "<run_dir>" [--model <m>] [--effort <e>]'
```

跑完會產生 `codex-review.md`，以及記錄結束碼和 session id 的 `codex-review.md.done.json`。

**Claude**（互動式 agent，保留審查脈絡給之後質詢用）：

```bash
herdr agent start review-claude --kind claude --pane <A> -- --add-dir "<run_dir>" [--model <m>] [--effort <e>]
herdr agent prompt review-claude "/code-review high <base>...HEAD"
herdr agent prompt review-claude "code review 全部完成後（包含背景審查），把最終 findings 原文寫到 <run_dir>/claude-review.md：每條含等級、file:line、問題、觸發情境、來源、同類位置。等級用 P0–P3，定義與 Codex review 相同：P0 必須立刻處理，會阻擋發布或主要使用；P1 緊急，應在下一輪處理；P2 一般，終究要修；P3 低，可有可無的改善。review 原本的等級或排序依這套定義換算，每條依自己的影響獨立判斷，不按名次分配，全部落在同一級也可以。review 有給 verdict（例如 CONFIRMED／PLAUSIBLE）時照抄。來源：有問題的程式碼在 <base> 就已存在寫「既有問題」，由本次變更造成寫「本分支引入」。同類位置：搜尋 repo 中沿用相同寫法、會有同樣問題的其他位置，列出 file:line，沒有就寫「無」。沒有問題就寫「無 findings」。最後一行寫 <!-- REVIEW-END -->。這是暫存檔，用一般 UTF-8 寫入即可，不必處理 BOM 或換行格式。還沒審完就等審完再寫，除了這個檔案不要修改任何東西。"
```

`agent prompt` 回傳的 `agent_session.value` 是 Claude 的 session id，記下來，報告會用到。

`agent start` 之後、送第一個 prompt 之前，先用 `herdr agent read review-claude --source visible --lines 20` 看一次畫面。Herdr 可能把啟動時的選單誤判成就緒，直接送 prompt 會把文字打進選單。
- 如果是更新提示，選「只跳過這次更新」之類的選項，不要更新，也不要長期略過更新。
- 如果是其他選單或確認畫面，照第 3 步 `blocked` 的方式處理，交給使用者。

名稱 `review-claude` 已被占用時改用 `review-claude-2`，後續指令都用同一個名稱。第二個 prompt 送出時 Claude 可能還在忙，Claude Code 會先排隊，等手上的事做完再處理。審查有沒有完成一律看檔案，不看 agent 狀態：`/code-review` 會把審查丟到背景，agent 顯示 idle 時審查可能還在跑。

## 3. 等待：用腳本阻塞，不要看 pane

```bash
python "SKILL_DIR/scripts/wait_for.py" \
  --marker-file "<run_dir>/claude-review.md" \
  --exists "<run_dir>/codex-review.md.done.json" \
  --agent review-claude --timeout-sec <秒數>
```

腳本等待期間不輸出任何東西，結束時只印一行 JSON。

- 如果你能把指令放到背景執行、結束時自動收到通知（例如 Claude Code 的 `run_in_background`），就用背景執行，`--timeout-sec 3600`。等待期間不要做任何事。
- 否則在前景執行，`--timeout-sec 540`。拿到 `timeout` 就原樣再呼叫一次。
- 等待期間不要用 `herdr agent read` 或 `pane read` 看進度，那會把一整頁終端機畫面讀進 context。

依結果處理：

- `done`：進入第 4 步。
- `blocked`：審查者停在授權或提問畫面。這時才用 `herdr agent read <name> --source recent-unwrapped --lines 30` 看是什麼，轉告使用者，由使用者自己去那個 pane 回應。不要替使用者按同意。處理完再重新等待。
- `missing`：審查者已結束。告知使用者，然後用現有的結果繼續。

## 4. 比對兩份結果

`claude-review.md` 和 `codex-review.md` 各讀一次。Codex 的 `done.json` 如果 `exit_code` 不是 0，或輸出裡沒有審查內容，就讀 `codex-review.log` 最後 30 行找原因。這種情況下 Codex 視為失敗，只用 Claude 的結果出報告並註明，不做質詢。

報告要忠於兩位審查者的原始結果。你只負責配對、排序；不重新評級，不刪除條目，也不合併同一位審查者自己列出的條目。

等級一律用 P0–P3：Claude 的照 `claude-review.md`，Codex 的照 `codex-review.md` 每條的 `[P0]`–`[P3]` 標籤。原生 review 的格式會隨版本改變，遇到不是 P0–P3 的說法，就依語意歸到最接近的一級。

每條 finding 記下：發現者、等級、位置、摘要、Claude 的 verdict，以及審查者給的來源（本分支引入／既有問題）與同類位置。Codex 原生 review 不提供這兩項，它單方的條目由質詢回覆補上。

- **兩方都有**：兩位審查者指出的根因相同，就合成一條，行號不同也算。等級取兩方中較高的，發現者寫兩方。
- **只有一方**：保留原樣。P0–P2 送去質詢，P3 不送。

## 5. 交叉質詢：只跑一輪

沒有單方的 P0–P2 就跳過這一步。有的話，每一方只送一次批次清單：

1. 用 `SKILL_DIR/assets/crossexam-prompt.md` 產生兩個檔案。`{items}` 每條一行：`X1 | P? | file:line | 摘要`。
   - `<run_dir>/crossexam-to-claude.md`：放 Codex 單方抓到的問題。`{output_rule}` 寫：「把回覆寫到 `<run_dir>/crossexam-claude-answer.md`，最後一行寫 `<!-- REVIEW-END -->`。」
   - `<run_dir>/crossexam-to-codex.md`：放 Claude 單方抓到的問題。`{output_rule}` 寫：「直接把回覆當成最後的訊息，不要寫檔。」
2. 送出：

   ```bash
   herdr agent prompt review-claude "請讀 <run_dir>/crossexam-to-claude.md，照裡面的規則回覆。"
   herdr pane run <B> 'python "SKILL_DIR/scripts/codex_review.py" ask --prompt-file "<run_dir>/crossexam-to-codex.md" --out "<run_dir>/crossexam-codex-answer.md" --session <codex-review.md.done.json 的 session_id> [--model <m>] [--effort <e>]'
   ```

   `session_id` 如果是 null，就不帶 `--session`，腳本會改開一個新的唯讀 session。
3. 用第 3 步的方式等待：`--marker-file crossexam-claude-answer.md`、`--exists crossexam-codex-answer.md.done.json`。

質詢到此結束。不把回覆再轉給原本的提出方，也不開第二輪。

質詢結果原樣標在該條底下，由使用者判斷。回覆「不成立」或「不確定」的條目照樣留在原本的等級，不刪除、不調整等級，你也不需要讀程式碼裁決。質詢回覆附的來源與同類位置，併入該條的對應欄位。

## 6. 寫報告與收尾

用 `SKILL_DIR/assets/review-template.md` 產生 `<run_dir>/REVIEW.md`。它和 `run_dir` 裡的其他檔案都是暫存產物，用一般 UTF-8 寫入即可，不必另外轉 BOM 或換行格式。

- 標頭填入 `init_run.py` 的欄位與兩邊的 session id。沒有指定的模型或 effort 寫「預設」。
- 不分章節，每條用 `- [P1] 標題` 開頭的清單項目呈現，細節縮排在底下。依等級排序（P0 → P3）；同一級內依序排兩方都有、質詢成立、質詢不成立或不確定、未質詢的條目。沒有任何條目時寫「無 findings」。
- **發現者**：只有一方找到就寫那一方；兩方在第一輪都找到才兩個都寫。質詢時才同意的一方不算發現者。Claude 有 verdict 時附在名字後面，例如「Claude（PLAUSIBLE）」。
- **來源**：照抄審查者的判斷；兩方判斷不同時並列，例如「Claude：既有問題／Codex：本分支引入」。沒有任何一方判斷時寫「未判斷」。
- **同類位置**：合併兩方列出的位置；都沒有就省略這一行。
- **質詢**：只有送過質詢的條目才寫這一行。回覆不成立或不確定時，在前面加 ⚠，並附上對方的理由。
- 樣板裡的示範條目要換成實際內容。

最後用 `herdr pane close <B>` 關掉 Codex 的 pane。Claude 的 pane A 保留，使用者逐條討論時可以用 `herdr agent prompt <名稱>` 接著問審查者。然後回覆使用者：

- `REVIEW.md` 的完整路徑
- P0–P3 各幾條，以及 P0、P1 的標題
- 標了 ⚠ 的條目，這些要由使用者判斷
- Claude 審查者仍開著（名稱與 pane ID），討論完可以用 `herdr pane close <A>` 關掉

不要修改任何程式碼，要修哪些由使用者決定。
