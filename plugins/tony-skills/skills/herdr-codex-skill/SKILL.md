---
name: herdr-codex-skill
description: 經 Herdr 讓 Codex 執行指定的 skill（$name）或 slash 指令（/name）。agent 要透過 Herdr 把 skill 或 slash 指令交給 Codex 執行時使用。需 HERDR_ENV=1。
---

# Herdr 交 Codex 執行 skill

把呼叫端指定的 skill 或 slash 指令送進 Codex 執行。要跑哪個 skill、帶什麼參數由呼叫端決定，本 skill 只負責正確送達。Herdr 的一般用法（開 pane、讀畫面、等待）看原生 `herdr` skill。

## 前置

- `HERDR_ENV` 不是 `1` 就告知使用者並停止。
- 沿用既有的 Codex pane；沒有就照原生 `herdr` skill 開一個同層 pane，再 `herdr agent start <name> --kind codex --pane <pane>`，啟動後先讀一次畫面。

## 指令轉換

- **照指定的 skill 執行，不換成 Codex 內建的同類功能**（例如要求跑某個 code-review skill，不改跑 `codex review`）。
- Codex 的 skill 一律用 `$` 觸發：呼叫端給的 `/xxx` 若是 skill 而不是 Codex 的 slash 指令，改成 `$xxx`。
- 指令只給短名、或選單有多個同名候選時，選與完整名稱相符的那一個；對不上就停下來問使用者，不要猜。

## 分步輸入

不能用 `herdr agent prompt` 一次送整行：`$`、`/` 會叫出 Codex 的補全選單，開頭被選單吃掉，Codex 只收到後面的參數，當成一般需求開始動工。

1. `herdr pane send-text <pane> '$<skill 名稱>'`：只送觸發字元與名稱（slash 指令則為 `/<指令>`）。
2. `herdr agent read <name> --source visible`：確認選單選中的是目標（畫面出現該 skill 與 `enter insert`）。
3. `herdr pane send-keys <pane> enter`：插入選項，不會送出。
4. `herdr pane send-text <pane> ' <參數>'`
5. 再讀一次畫面，確認整行無誤。
6. `herdr pane send-keys <pane> enter`：送出。

## 送出之後

- 讀回應，確認 Codex 有照該 skill 的流程進行，再 `herdr agent wait <name>` 等待。看出誤解就立刻 `herdr agent send-keys <name> esc` 中斷並回報使用者。
- 等待期間不要反覆讀畫面看進度。
- 完成後用 `herdr agent read <name> --source recent-unwrapped` 讀結果回報使用者，並附上 pane ID；pane 保留不關，方便接著問。

## pane 操作界線

Codex 停在選單、授權或提問畫面時，只把畫面內容轉告使用者，由使用者自己到 pane 回應，不代按。唯一例外：本 skill 開的 Codex 跳出更新提示，一律選 Skip。
