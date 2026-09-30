## 安裝教程

本 repository 為 public，Claude Code 與 Codex 都可以直接從 GitHub 安裝，不需要先 clone。

> repository 為 `Hon-Lu/skills`，marketplace 與 plugin 名稱都是 `tony-skills`（取自 `.claude-plugin/marketplace.json` 的 `name`）。
> `marketplace add` 給的是 GitHub repository，其後的 install / update / remove 一律用 `tony-skills`。

### Claude Code 安裝/更新/移除 指令說明

安裝指令（於終端開啟 Claude CLI 後，依序輸入以下指令）：
```
/plugin marketplace add Hon-Lu/skills
```
```
/plugin install tony-skills@tony-skills
```
```
/reload-plugins
```

更新指令：
```
/plugin marketplace update tony-skills
```
```
/reload-plugins
```

移除指令：
```
/plugin uninstall tony-skills
```
```
/plugin marketplace remove tony-skills
```

### Codex 安裝/更新/移除 指令說明

安裝指令（開啟終端後直接輸入）：
```powershell
codex plugin marketplace add Hon-Lu/skills
```
```powershell
codex plugin add tony-skills@tony-skills
```

更新指令（先更新 marketplace 快照，再重新 add 一次 plugin）：
```powershell
codex plugin marketplace upgrade tony-skills
```
```powershell
codex plugin add tony-skills@tony-skills
```

移除指令：
```powershell
codex plugin remove tony-skills@tony-skills
```
```powershell
codex plugin marketplace remove tony-skills
```

確認目前安裝狀態：
```powershell
codex plugin list
```

### 從本機路徑安裝改為 GitHub 安裝

之前以 `C:\tools\skills` 本機路徑安裝過的，先照上方的移除指令移除 plugin 與 marketplace，再用 GitHub 的方式重新安裝。
兩種來源的 marketplace 名稱都是 `tony-skills`，不先移除會衝突。

### 前置需求

`herdr-dual-review` 需要 Herdr、Claude Code CLI、Codex CLI 與 Python 3，主 agent 必須在 Herdr 的 pane 裡執行。
