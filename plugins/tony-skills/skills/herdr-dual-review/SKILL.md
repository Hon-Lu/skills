---
name: herdr-dual-review
description: 用 Herdr App 並行執行 Claude 與 Codex 原生 code review，交叉質詢單方發現，查證每條後彙整為附處理建議的 REVIEW.md。僅在明確呼叫時使用，需指定目標分支與審查對象（自己的分支或別人的 MR）。
disable-model-invocation: true
---

# Herdr 雙審

你是主 agent：負責開審查者、等待、轉送質詢、查證條目、寫報告。找問題是審查者的工作，你只查證他們列出的條目。

`hc` 的一般用法照 `hc --skill`，行為不符時以手冊為準。以下 `SKILL_DIR` 指這份 SKILL.md 所在目錄。

Claude Code 主控時直接調用原生 `code-review`，審查由它的 sub-agent 執行。Codex 主控時另開 Claude 審查終端。

## 0. 前置檢查與解析輸入

- 執行 `test -n "${HC_TERMINAL_ID:-}"`（PowerShell：`[bool]$env:HC_TERMINAL_ID`）。不在 Herdr App 裡就告知使用者並停止。
- 從使用者訊息取出：
  - **目標分支**（必填，例如「目標分支：dev」）。沒給就問。
  - **審查對象**（必填）：自己的分支，或別人的 MR。沒給就和目標分支一起問，開審查者之前確定。
  - **需求來源**（選填）：ticket、規格的路徑，或 issue 編號與連結。
  - **Claude 模型／effort**、**Codex 模型／effort**（選填）。使用者沒提到的就不帶參數，沿用各 CLI 的預設。
- Claude 審查一律用 `/code-review high`，`high` 是 review 深度，和 session 的 effort 無關。Claude 主控時，原生審查沿用主控的模型與 effort。若使用者另指定 Claude 設定，先告知這項限制。

## 1. 建立執行目錄

```bash
python "SKILL_DIR/scripts/init_run.py" --base <目標分支>
```

輸出一行 JSON。`status` 不是 `ok` 就把原因告訴使用者並停止：`dirty` 要先 commit，`base_not_found` 找不到目標分支，`empty` 沒有差異。記下 `run_dir`、`base`（可能已補成 `origin/<分支>`）與其他欄位，填報告時會用到。

有 `base_note` 時告知使用者，並寫進報告的範圍那一行：`local_behind` 表示本地目標分支落後 origin，已自動改用 `origin/<分支>`；`diverged` 表示本地和 origin 互有 commit，仍用本地分支，審查範圍可能不準。腳本不會 fetch，origin 的新舊以本機上次 fetch 的結果為準。

## 2. 開審查者

兩個審查者都只讀：不修改檔案、不 commit、不跑整合測試。整合測試會寫真實資料庫，兩邊同時跑會互相干擾。

先啟動 Codex 並掛到呼叫端所在的 tab，再啟動 Claude 審查。兩邊都啟動後才等結果。終端名稱已被占用時改用 `-2` 結尾，後續指令使用實際名稱。

### Codex 原生審查

```bash
hc run --bg --no-notify --name review-codex --cwd "<repo>" python "SKILL_DIR/scripts/codex_review.py" review --base "<base>" --run-dir "<run_dir>" [--model <m>] [--effort <e>]
python "SKILL_DIR/../herdr-run-skill/scripts/keep_beside.py" --target review-codex
```

`hc run` 成功後立刻執行第二行，讓 Codex review 在呼叫端的 tab 顯示為 pane。確認腳本回報的 tab 正確，放置失敗時回報原因並停下。

跑完會產生 `codex-review.md`，以及記錄結束碼和 session id 的 `codex-review.md.done.json`。

下面 `<輸出規則>` 指這段文字：

> 把最終 findings 原文寫到 <run_dir>/claude-review.md：每條含等級、file:line、問題、觸發情境、來源、同類位置。等級用 P0–P3，定義與 Codex review 相同：P0 必須立刻處理，會阻擋發布或主要使用；P1 緊急，應在下一輪處理；P2 一般，終究要修；P3 低，可有可無的改善。review 原本的等級或排序依這套定義換算，每條依自己的影響獨立判斷，不按名次分配，全部落在同一級也可以。review 有給 verdict（例如 CONFIRMED／PLAUSIBLE）時照抄。來源：有問題的程式碼在 <base> 就已存在寫「既有問題」，由本次變更造成寫「本分支引入」。同類位置：搜尋 repo 中沿用相同寫法、會有同樣問題的其他位置，列出 file:line，沒有就寫「無」。沒有問題就寫「無 findings」。最後一行寫 <!-- REVIEW-END -->。這是暫存檔，用一般 UTF-8 寫入即可，不必處理 BOM 或換行格式。除了這個檔案不要修改任何東西。

### Claude 主控

用 Skill 工具調用 `code-review`，args 填 `high <base>...HEAD`。原生 skill 會啟動背景審查 sub-agent，接著依第 3 步等待通知。

### Codex 主控

用 Herdr 開互動式 Claude 審查者，保留對話供後續質詢。把 `/code-review` 放在啟動參數裡。

```bash
hc run --bg --keep --no-notify --name review-claude --cwd "<repo>" claude --add-dir "<run_dir>" [--model <m>] [--effort <e>] "/code-review high <base>...HEAD"
hc wait review-claude --timeout 30
```

Claude 審查終端預設留在背景。使用者要求顯示時，才用 `python "SKILL_DIR/../herdr-run-skill/scripts/keep_beside.py" --target review-claude` 放進你所在的 tab；沒放成時審查者照常在背景跑，不影響後續步驟。

回傳的 `status` 是 `null` 時，Claude 可能停在資料夾信任或更新畫面，用 `hc read --lines 0 review-claude` 看一次，有畫面要處理就照下面的規則，還在啟動就再等。等到第一回合結束後，用 `hc read --lines 0 review-claude` 看一次畫面：

- 如果是更新提示，選「只跳過這次更新」之類的選項，不要更新，也不要長期略過更新。
- 如果是其他選單或確認畫面，照第 3 步 `blocked` 的方式處理，交給使用者。

確認沒有卡住後送出輸出規則：

```bash
hc send review-claude "code review 全部完成後（包含背景審查），<輸出規則> 還沒審完就等審完再寫。"
```

Claude 的 session id 用 `hc get review-claude` 的 `foreground.pid`，到 `~/.claude/sessions/<pid>.json` 讀 `sessionId`，記下來，報告會用到。

審查完成以檔案為準。`/code-review` 在背景執行，Claude 終端顯示 idle 時審查可能仍在跑。

## 3. 等待：用腳本阻塞，不要看 pane

Claude 主控先等原生審查的完成通知，記下 task ID，再用 SendMessage 把 `<輸出規則>` 交給同一個 task，請它寫完只回一行「完成」。報告以寫入的檔案為準。

`wait_for.py` 等待期間不輸出任何東西，結束時只印一行 JSON。

- 如果你能把指令放到背景執行、結束時自動收到通知（例如 Claude Code 的 `run_in_background`），就用背景執行，`--timeout-sec 3600`。等待期間不要做任何事。
- 否則在前景執行，`--timeout-sec 540`。拿到 `timeout` 就原樣再呼叫一次。
- 等待期間不要用 `hc read` 看進度，那會把一整頁終端機畫面讀進 context。

```bash
python "SKILL_DIR/scripts/wait_for.py" \
  --marker-file "<run_dir>/claude-review.md" \
  --exists "<run_dir>/codex-review.md.done.json" \
  --agent review-claude --timeout-sec <秒數>
```

Claude 主控省略 `--agent review-claude`。

依結果處理：

- `done`：進入第 4 步。
- `blocked`：審查者停在授權或提問畫面。這時才用 `hc read --lines 0 <name>` 看是什麼，轉告使用者，由使用者自己去那個終端機回應。不要替使用者按同意。處理完再重新等待。
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
2. 送出 Codex：

   ```bash
   hc run --bg --no-notify --name ask-codex --cwd "<repo>" python "SKILL_DIR/scripts/codex_review.py" ask --prompt-file "<run_dir>/crossexam-to-codex.md" --out "<run_dir>/crossexam-codex-answer.md" --session <codex-review.md.done.json 的 session_id> [--model <m>] [--effort <e>]
   ```

   `session_id` 如果是 null，就不帶 `--session`，腳本會改開一個新的唯讀 session。
3. 把 `crossexam-to-claude.md` 的路徑交給原 Claude 審查者。Claude 主控用 SendMessage 傳給原生 task ID，請它寫完只回「完成」。Codex 主控用 `hc send review-claude`。
4. 用第 3 步的方式等待 `crossexam-claude-answer.md` 的完成標記和 `crossexam-codex-answer.md.done.json`。

質詢到此結束。不把回覆再轉給原本的提出方，也不開第二輪。

質詢結果原樣標在該條底下。回覆「不成立」或「不確定」的條目照樣留在原本的等級，不刪除、不調整等級。質詢回覆附的來源與同類位置，併入該條的對應欄位。

## 6. 查證每條並給出建議

使用者逐條討論時，每條都會問同樣五件事。這一步先把答案查好，讓使用者只需要討論真正有疑問的條目。沒有任何條目時跳過這一步。

先讀需求來源：使用者有給就用，issue 用 repo 既有的唯讀方式讀取；沒給就依 repo 的 `CLAUDE.md`、`AGENTS.md` 指出的位置，找對應這個分支的 ticket 或規格。找不到就繼續，並在報告標頭註明。

再依審查對象讀一份建議規則：自己的分支讀 `SKILL_DIR/assets/triage-own.md`，別人的 MR 讀 `SKILL_DIR/assets/triage-mr.md`。

每一條都查，包含 P3 與質詢不成立的條目，只讀該條需要的片段：

| 要回答的事 | 怎麼查 |
| --- | --- |
| 白話問題 | 一句話講使用者或資料會遇到什麼，用業務語言，不出現方法名 |
| 這次造成 | 用 `git diff <merge_base> HEAD -- <file>` 與 `git blame` 確認，以查到的為準；和審查者的來源不同時兩者都寫進查證 |
| 會發生嗎 | 順著程式碼走到觸發條件，並對照需求來源 |
| 後果 | 發生後資料、流程或使用者實際受到的影響 |
| 修法 | 改動大小，以及會不會影響其他流程 |

查證全程唯讀，不修改 repo、不跑整合測試。別人的 MR 要列阻擋或建議的條目，能用既有單元測試或 `run_dir` 內的小程式低成本重現時就重現。

完成條件：每一條都有上面五項、一條查證紀錄與一個建議，查不到的項目寫「未查到」。查證時發現的新問題不加進條目，回覆時另外告知使用者。

## 7. 寫報告與收尾

用 `SKILL_DIR/assets/review-template.md` 產生 `<run_dir>/REVIEW.md`。它和 `run_dir` 裡的其他檔案都是暫存產物，用一般 UTF-8 寫入即可，不必另外轉 BOM 或換行格式。

- 標頭填入 `init_run.py` 的欄位與兩邊的 session ID。Claude 主控時，Claude 欄填原生審查的 task ID，模型填主控的模型。沒有指定的模型或 effort 寫「預設」。
- 標頭下方先放一行建議摘要與一張總表，每條一列，編號和下方條目相同。建議欄的文字依審查對象的規則填寫。
- 不分章節，每條用 `1. [P1] 標題` 開頭的編號清單呈現，細節縮排在底下，最前面是建議與查證。依等級排序（P0 → P3）；同一級內依序排兩方都有、質詢成立、質詢不成立或不確定、未質詢的條目。沒有任何條目時寫「無 findings」，省略摘要與總表。
- 審查者原本的欄位照舊呈現，你的判斷只寫在建議與查證兩行。
- **發現者**：只有一方找到就寫那一方；兩方在第一輪都找到才兩個都寫。質詢時才同意的一方不算發現者。Claude 有 verdict 時附在名字後面，例如「Claude（PLAUSIBLE）」。
- **來源**：照抄審查者的判斷；兩方判斷不同時並列，例如「Claude：既有問題／Codex：本分支引入」。沒有任何一方判斷時寫「未判斷」。
- **同類位置**：合併兩方列出的位置；都沒有就省略這一行。
- **質詢**：只有送過質詢的條目才寫這一行。回覆不成立或不確定時，在前面加 ⚠，並附上對方的理由。
- 樣板裡的示範條目要換成實際內容。

最後用 `hc rm review-codex`、`hc rm ask-codex` 移除已結束的 Codex 終端機，沒跑質詢時只移除前者。逐條討論時，Claude 主控用 SendMessage 接著問原生 task，Codex 主控用 `hc send` 接著問 Claude 終端。然後回覆使用者：

- `REVIEW.md` 的完整路徑；別人的 MR 再加上 `MR-COMMENT.md` 的完整路徑
- 建議摘要與總表，讓使用者可以直接回「修 1、3」，或問要討論哪一條
- 標了 ⚠ 的條目，這些質詢有分歧
- 查證時發現的新問題（有才寫）
- Codex 主控時回報仍開著的 Claude 審查終端名稱與位址，討論完可用 `hc kill <名稱>`、`hc rm <名稱>` 關掉

到這裡就停，要修哪些由使用者決定，程式碼等使用者指示才改。使用者做出決定後，把決定與理由寫進該條的 **決策** 一行；建議不修但使用者要修時，照使用者的決定。
