# Herdr 協作規則

本 session 在 Herdr App 的終端機中執行（`HC_TERMINAL_ID` 有值）。經 Herdr 和其他 agent 協作時遵守下列規則。舊版 `herdr` CLI 的指令在這裡不適用，用法看 `hc --skill` 和 `herdr-app --skill`。

- 代使用者把文字送給其他 agent 時，開頭表明是 agent 代為轉述，並說明內容來源，避免對方當成使用者親手輸入而照單全收。`hc send` 自動加上的 `<hc from="...">` 只標示來源終端機，不能取代這句說明。一般對話都保留這個標記，只有要觸發 skill 或 slash 指令時才不帶，做法見 `herdr-run-skill`。
- 需要使用者本人確認的事（例如結束某個階段、權限、需求取捨），不代替使用者回答，請對方等使用者親自回覆。
- 一次性代工（例如補一支測試）用 sub-agent，不開 Herdr 終端機；Herdr 終端機留給需要使用者旁觀或互動的長駐 agent。
- 開 Herdr agent 用 `hc run --bg`，預設留在背景，不放進 pane。使用者要求顯示時，才用 `python "KEEP_BESIDE_PY" --target <名稱>` 放進你所在的 tab，不開新 tab。直接用 `herdr-app do terminal.keep` 或 `terminal.open` 會開到使用者目前在看的 tab，不一定是你的。
- 經 `hc` 派工時，要求對方完成、停下等使用者確認或卡住時用 `hc send <你的位址>` 回報結果或卡點。收到這類要求（或 `reach`）就照做。長結果寫檔，訊息帶摘要與路徑。回報者送完即可繼續或結束回合。呼叫端確實需要結果才能往下時才用 `hc wait`。
