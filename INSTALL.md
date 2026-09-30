## 安裝教程

本 repository 為 private，plugin 指令無法直接從 GitHub 取得，
因此採**先 clone 到本機、再以本機路徑安裝**的方式。

### 取得 repository

```powershell
git clone https://github.com/Hon-Lu/skills.git C:\tools\skills
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

> [!IMPORTANT]
> Codex 的本機 marketplace 路徑**必須使用正斜線**。
> 傳入 `C:\tools\skills` 會被判定為 `invalid marketplace source format`，要寫成 `C:/tools/skills`。

安裝指令 (開啟 Command 終端後直接輸入)：
```powershell
codex plugin marketplace add C:/tools/skills
```
```powershell
codex plugin add tony-skills@tony-skills
```

更新指令 (先更新本機 repository，再重新 add 一次 plugin)：
```powershell
git -C C:\tools\skills pull
```
```powershell
codex plugin add tony-skills@tony-skills
```

> `codex plugin marketplace upgrade` **只適用 Git marketplace**，對本機路徑的 marketplace 會回
> `marketplace is not configured as a Git marketplace`，更新時不需要也不能執行。
> 本機 marketplace 的 root 直接指向 `C:\tools\skills`，`git pull` 後再 `plugin add` 就會裝上新版本。

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

> repository 名稱為 `skills`，marketplace 名稱為 `tony-skills`（取自 `.claude-plugin/marketplace.json` 的 `name`）。
> 因此 `marketplace add` 給的是本機路徑，其後的 install / update / remove 一律用 `tony-skills`。

### 若日後改為公開，或設定好 SSH

repository 轉為 public 後，可直接用簡寫安裝，不必先 clone：

```
/plugin marketplace add Hon-Lu/skills
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

`herdr-dual-review` 需要 Herdr、Claude Code CLI、Codex CLI 與 Python 3，主 agent 必須在 Herdr 的 pane 裡執行。
