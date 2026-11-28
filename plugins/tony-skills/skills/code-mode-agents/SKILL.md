---
name: code-mode-agents
description: 用 hc（herdr-core）開 Claude 子 agent 前使用：決定要不要讓它以 Code Mode（實驗功能，Claude 寫 JavaScript 一次呼叫多個工具）啟動，以及怎麼開。只要是 `hc run ... claude` 派工就先看這份。需在 Herdr App 的終端機內（HC_TERMINAL_ID 有值）。
---

# 子 agent 要不要開 Code Mode

## 判斷（拿不準就不開）
開：
- 大量讀碼、搜尋、整理資料的調查任務（工具呼叫多、彼此獨立）。
- 單純改程式＋跑測試，沒有實機操作。

不開：
- 要開 app、送按鍵、移游標、截圖的實機測試：每一步前都要確認前景／範圍，Code Mode 會把多步包成一段一次跑完。
- 要用 Claude in Chrome、computer use、Remote Control 的任務（Code Mode 下這些都關閉）。
- 長駐的協調者 session（Code Mode 開的 session 之後只能在 Code Mode 下 resume）。

## 怎麼開
只能用 hc 開獨立的 `claude` 行程；內建 Agent 工具的 sub-agent 只有在父 session 本身是 Code Mode 時才能用（工具清單加 `REPL`）。

```bash
hc run --bg --keep --json --name <名稱> --cwd "<信任過的資料夾>" \
  claude --settings '{"env":{"CLAUDE_CODE_EXPERIMENTAL_CODE_MODE":"1"}}' [--model <m>] '<派工內容>'
```

- 用 `--settings` 帶環境變數；`hc run env X=1 ...` 在 Windows 找不到 env。
- 不開就把 `--settings ...` 拿掉，其餘照常。
- cwd 要是信任過的資料夾，否則會卡在 trust 提示。
- 啟動後 `hc read <名稱>`：出現「Code Mode (experimental)」確認畫面，代表使用者還沒首次啟用過——不要代選；關掉它、改用不開的方式重派，並告訴使用者要自己在終端機確認一次。
- 之後要 `--resume`／`--continue` 那個 agent，啟動指令要帶同一個 `--settings`。
- 派工單與回報裡寫明這個 agent 有沒有開 Code Mode。
