## 安裝教程

### Claude Code 安裝/更新/移除 指令說明

安裝指令 (於終端開啟 Claude Cli 後，依序輸入以下指令)：
```
/plugin marketplace add asd880921/skills
```
```
/plugin install tony-skills
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

安裝指令 (開啟 Command 終端後直接輸入)：
```powershell
codex plugin marketplace add asd880921/skills
```
```powershell
codex plugin add tony-skills@tony-skills
```

更新指令：
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

> repository 名稱為 `skills`，marketplace 名稱為 `tony-skills`（取自 marketplace.json 的 `name`）。
> 因此 `marketplace add` 用 `asd880921/skills`，其後的 update / remove 一律用 `tony-skills`。

### 前置需求

`mr-review` 掛在 [Matt Pocock 的 skills](https://github.com/mattpocock/skills) 上運作，安裝前請先具備該套 skill。
搭配 [support-matt](https://github.com/asd880921/support-matt) 使用時功能完整；未安裝時 `mr-review` 仍可運作，但只走模式 B。
