# Herdr 協作規則

本 session 在 Herdr App 的終端機中執行（`HC_TERMINAL_ID` 有值）。經 Herdr 和其他 agent 協作時遵守下列規則。舊版 `herdr` CLI 的指令在這裡不適用，用法看 `hc --skill` 和 `herdr-app --skill`。

- 代使用者把文字送給其他 agent 時，開頭表明是 agent 代為轉述，並說明內容來源，避免對方當成使用者親手輸入而照單全收。`hc send` 自動加上的 `<hc from="...">` 只標示來源終端機，不能取代這句說明。
- 需要使用者本人確認的事（例如結束某個階段、權限、需求取捨），不代替使用者回答，請對方等使用者親自回覆。
- 一次性代工（例如補一支測試）用 sub-agent，不開 Herdr 終端機；Herdr 終端機留給需要使用者旁觀或互動的長駐 agent。
