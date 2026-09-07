## 安裝教程

本 repository 為 private，plugin 指令無法直接從 GitHub 取得，
因此採**先 clone 到本機、再以本機路徑安裝**的方式。

### 取得 repository

```powershell
git clone https://github.com/asd880921/skills.git C:\tools\skills
```

路徑可自訂，以下指令一律以 `C:\tools\skills` 為例；換路徑時同步替換。

### Claude Code 安裝/更新/移除 指令說明

安裝指令 (於終端開啟 Claude Cli 後，依序輸入以下指令)：
```
/plugin marketplace add C:\tools\skills
```
```
/plugin install tony-skills
```
```
/reload-plugins
```

更新指令 (先在終端更新本機 repository，再回 Claude Cli)：
```powershell
git -C C:\tools\skills pull
```
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
codex plugin marketplace add C:\tools\skills
```
```powershell
codex plugin add tony-skills@tony-skills
```

更新指令：
```powershell
git -C C:\tools\skills pull
```
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

> repository 名稱為 `skills`，marketplace 名稱為 `tony-skills`（取自 `.claude-plugin/marketplace.json` 的 `name`）。
> 因此 `marketplace add` 給的是本機路徑，其後的 install / update / remove 一律用 `tony-skills`。

### 若日後改為公開，或設定好 SSH

repository 轉為 public 後，可直接用簡寫安裝，不必先 clone：

```
/plugin marketplace add asd880921/skills
```

維持 private 但想省略 clone 步驟時，需將本機公鑰加入 GitHub 帳號
（`Settings` → `SSH and GPG keys`），Claude Code 對 private repository 會改走 SSH：

```powershell
type $env:USERPROFILE\.ssh\id_ed25519.pub
```

首次連線前需先信任 GitHub 的 host key，並核對指紋與官方公布值相符：

```powershell
ssh -T git@github.com
```

### 前置需求

`mr-review` 掛在 [Matt Pocock 的 skills](https://github.com/mattpocock/skills) 上運作，安裝前請先具備該套 skill。
搭配 [support-matt](https://github.com/asd880921/support-matt) 使用時功能完整；未安裝時 `mr-review` 仍可運作，但只走模式 B。
