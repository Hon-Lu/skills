# Code Review 規則

走完 `SKILL.md` 的補充審查重點後讀本文件，逐面向核對本次 diff。

**只套用 diff 實際涵蓋的面向**，不推測 diff 以外不存在的程式碼；命中的候選一律回到 `SKILL.md` 的證據門檻逐條驗證，未通過不得輸出。第 1 至 5 節與技術無關，第 6 節為技術別補充，只在專案使用該技術時適用。

---

## 1. 正確性

| 檢查 | 嚴重度 |
| --- | --- |
| Off-by-one、邊界條件錯誤 | P1 |
| 可由 diff 直接判斷的邏輯錯誤 | P1 |
| 取值前缺少 null 或空集合檢查 | P2 |
| 非同步路徑的未處理例外 | P2 |
| 回傳與實際結果不符的 HTTP status code | P2 |

## 2. 資安（OWASP）

| 檢查 | OWASP | 嚴重度 |
| --- | --- | --- |
| 查詢語句由字串拼接使用者輸入組成，未使用參數化查詢 | A03 Injection | P0 |
| Token、密碼、PII 等敏感資料寫入 log 或出現在 response | A02 Crypto | P0 |
| 新增的 endpoint 缺少授權檢查 | A01 Access Control | P0 |
| 使用者傳入的 ID 未做資源擁有權驗證 | A01 Access Control | P1 |
| 請求直接繫結至領域模型，未經 DTO 或欄位白名單過濾 | A08 Mass Assignment | P2 |
| 系統邊界缺少輸入驗證 | A03 Injection | P2 |

## 3. 資料存取與交易

| 檢查 | 嚴重度 |
| --- | --- |
| Schema 異動缺少對應的 migration 或版本控管腳本 | P1 |
| 多步驟寫入缺少交易包裹 | P1 |
| N+1 查詢（迴圈中逐筆呼叫資料庫） | P2 |
| 新欄位用於 `WHERE` 或 `JOIN` 但缺少索引 | P2 |

**交易風險細則：**

| 情境 | 嚴重度 | 說明 |
| --- | --- | --- |
| 多次獨立寫入未包在同一交易內 | P1 | 部分成功即資料不一致 |
| 寫入成功後呼叫外部 API 或發送訊息，但無補償機制 | P1 | 外部副作用不可回滾 |
| 單次寫入，但方法名稱暗示多步驟操作（例如 `CreateOrderAndSendNotification`） | P2 | 確認是否需要 outbox 或 saga |
| 讀取後寫入，缺少樂觀鎖（版本或時間戳欄位） | P2 | Lost update 風險 |
| 交易隔離等級為 read uncommitted | P2 | Dirty read 風險 |

## 4. API 向後相容性

重點是保護**外部 consumer**（前端、第三方、App）不受 server-side 變更影響。

破壞性變更一律 **P0**：

| 異動類型 | 範例 |
| --- | --- |
| 回應模型移除對外欄位 | `paymentType` 被刪除 |
| 回應模型欄位改名 | `paymentType` → `paymentCategory` |
| 回應模型欄位型別改變 | 數值 → 字串 |
| Route 移除或路徑改變 | `v1/orders` 變更 |
| HTTP method 改變 | `GET` → `POST` |
| 新增必填請求參數且無預設值 | 新增 `required` 欄位 |
| enum 值移除 | `Cash` 被刪除 |

可向後相容但仍需提醒：

| 異動類型 | 嚴重度 | 說明 |
| --- | --- | --- |
| enum 新增值 | P2 | consumer 的分支處理需確認有 default |
| 回應模型新增選填欄位 | P3 | consumer 不需改動，但提醒前端更新 |
| 新增 endpoint、請求新增有預設值的選填欄位 | P3 | 無影響 |

判斷破壞性變更時，優先檢視對外契約檔案的移除行（`-` 開頭）。

## 5. 程式碼品質

| 檢查 | 嚴重度 |
| --- | --- |
| 死碼（不可達分支、未使用變數） | P2 |
| 命名不符合既有程式碼或 `CONTEXT.md` 的既有慣例 | P2 |
| 單一方法過長且無明確理由 | P3 |
| 魔法數字或字串應改為常數或列舉 | P3 |
| 重複邏輯應抽出共用 | P3 |

## 6. 技術別補充

### .NET / C#

只在專案為 .NET / C# 時適用。

| 檢查 | 嚴重度 |
| --- | --- |
| async 方法使用 `.Result` 或 `.Wait()` 阻塞（deadlock 風險） | P1 |
| `Task` 未 `await` | P1 |
| `IDisposable` 型別未以 `using` 釋放 | P2 |
| `catch (Exception)` 過於廣泛且未重拋或記錄 | P2 |
| Library 層級缺少 `ConfigureAwait(false)` | P3 |

對應上面各節的具體形式：

| 通用規則 | .NET / EF Core / Dapper 的具體形式 |
| --- | --- |
| 參數化查詢（第 2 節） | Dapper 必須使用參數，不得字串拼接進原始 SQL |
| DTO 或白名單過濾（第 2 節） | 使用 `[Bind]` 或獨立 DTO，不直接繫結 Domain Entity |
| 多次獨立寫入未包在同一交易內（第 3 節） | 多個 `DbContext.SaveChanges()` 未以 `TransactionScope` 或 `BeginTransaction` 包裹 |
| 樂觀鎖（第 3 節） | 缺少 `RowVersion` 或 `Timestamp` 欄位 |
| Route 與必填參數（第 4 節） | `[Route]` 變更、新增 `[Required]` 參數 |

檢視破壞性變更的起點：

```bash
git diff <target>..HEAD -- '**/*Dto.cs' '**/*Response.cs' '**/*Controller.cs' | grep '^-.*public'
```
