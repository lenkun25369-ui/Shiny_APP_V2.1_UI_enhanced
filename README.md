# Shiny APP：CHARM 住院死亡風險評分介面

以 **Shiny for Python** 建立的互動式儀表板，針對疑似敗血症情境，依五個二元臨床因子查表顯示 CHARM 住院死亡風險。介面為英文，可手動輸入，也可接收外部啟動器提供的 FHIR 參數，自動帶入部分資料後再調整。

> 本專案是評分介面與 FHIR 串接原型，不包含模型訓練，也不是已完成臨床驗證的醫療產品。顯示百分比來自程式內固定對照表，不能視為個別病人的確定預後。使用真實醫療資料前，請先處理下方安全性與資料語意限制。

## 功能

- 五項 Yes／No 輸入與即時分數計算。
- 顯示估計風險百分比、風險標籤、漸層風險條及各項因子狀態。
- 透過 Bearer token 讀取 FHIR Patient，以及選填的單一 Observation。
- 將 Observation 的 component 值帶入欄位；使用者仍可手動修改。
- 展開檢視取得的 Patient／Observation JSON。
- 提供 Render 部署設定。

## 專案結構

```text
.
├── app.py             # UI、評分表、FHIR 讀取與欄位對應
├── requirements.txt   # Python 套件
├── render.yaml        # Render Web Service 設定
└── README.md
```

## 本機啟動

需先安裝 Python、pip；若使用 clone 指令，另需 Git。儲存庫目前未指定 Python 版本，也沒有完整鎖定所有相依套件。

```bash
git clone https://github.com/lenkun25369-ui/Shiny_APP_V2.1_UI_enhanced.git
cd Shiny_APP_V2.1_UI_enhanced
python -m venv .venv
```

啟用虛擬環境：

```bash
# Linux / macOS / WSL
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

安裝並啟動：

```bash
python -m pip install -r requirements.txt
python -m shiny run --host 127.0.0.1 --port 8000 app.py
```

瀏覽器開啟 http://127.0.0.1:8000 。

不帶 FHIR 參數時，程式不發出 FHIR 請求，可直接以五項輸入操作；資料檢視區會顯示空物件。若系統的 Python 指令是 `python3`，請相應替換。

### 套件

| 套件 | 儲存庫設定 | 用途 |
| --- | --- | --- |
| shiny | `==0.7.1` | Python Web UI 與 reactive 邏輯 |
| htmltools | `>=0.6.0` | HTML UI 相依套件 |
| uvicorn | 未鎖版 | ASGI 服務 |
| requests | 未鎖版 | FHIR HTTP 請求 |

## 評分與顯示規則

五項欄位選為 **Yes** 時各加一分，總分介於 0–5：

1. 無寒顫（UI 標示 `noChills (absence of Chills)`）。
2. 低體溫，體溫 < 36 °C。
3. 貧血，RBC < 4 M/µL。
4. RDW > 14.5%。
5. 惡性腫瘤病史。

程式中的固定對照表：

| 總分 | 顯示的住院死亡風險 |
| ---: | ---: |
| 0 | 0.36% |
| 1 | 1.89% |
| 2 | 5.79% |
| 3 | 12.97% |
| 4 | 23.58% |
| 5 | 34.15% |

UI 以 < 5%、5% 至 < 20%、≥ 20% 分別顯示 Very Low Risk、Moderate Risk、High Risk。這是目前程式的顯示分類，不代表本儲存庫另外驗證過的臨床分層。

程式附有 [PubMed 參考連結（PMID 27832977）](https://pubmed.ncbi.nlm.nih.gov/27832977/)。本文件依目前程式描述行為，未重新核對文獻中的模型定義、係數或適用族群。

## FHIR 啟動參數

目前不是完整的 SMART on FHIR OAuth 啟動流程。外部啟動器必須先取得授權，再將以下參數放入網址的 **fragment（`#` 後方）**；不是一般的 `?` query string。

| 參數 | 必要性 | 用途 |
| --- | --- | --- |
| `token` | FHIR 模式必要 | FHIR API 的 Bearer token |
| `pid` | FHIR 模式必要 | Patient resource ID |
| `fhir` | FHIR 模式必要 | FHIR base URL，建議不含結尾斜線 |
| `obs` | 選填 | 單一 Observation resource 的完整 URL |

僅表示結構的示意，請勿將真實 token 貼入公開文件：

```text
http://127.0.0.1:8000/#token=<ACCESS_TOKEN>&pid=<PATIENT_ID>&fhir=<FHIR_BASE_URL>&obs=<OBSERVATION_URL>
```

各參數值須適當 URL encode。頁面載入時，JavaScript 讀取 fragment 並傳給 Shiny 後端；後端使用相同 Bearer token 讀取：

- `{fhir}/Patient/{pid}`
- `obs` 指定的 URL（有提供時）

目前只讀取資料，不會寫回 FHIR／HIS，也不會自行搜尋最新檢驗、查詢 Observation Bundle 或更新 token。

### Observation component 對應

程式只檢查每個 component 的第一個 `code.coding` 項目：

| component code | 讀取欄位與條件 | UI 欄位 |
| --- | --- | --- |
| `chills` | `valueInteger == 1` | noChills → Yes |
| `malignancy` | `valueInteger == 1` | Malignancy → Yes |
| `789-8` | `valueQuantity.value < 4` | Anemia → Yes |
| `788-0` | `valueQuantity.value > 14.5` | RDW → Yes |
| `8310-5` | `valueQuantity.value < 36` | Hypothermia → Yes |

**請特別確認 `chills` 的語意：**程式將此 code 的 1 對應到「無寒顫 Yes」，名稱卻可能被解讀為「有寒顫」。資料產生端與接收端必須先確認一致，否則可能顛倒評分。README 僅揭露現況，沒有變更原程式。

程式也沒有檢查 coding system、檢驗單位、觀測時間或 Observation 是否屬於該病人。當有 component 資料時，各因子先預設為 No，未找到符合條件的值也會保留 No；**缺值不等於陰性**，使用者必須核對原始資料。

## Render 設定

`render.yaml` 目前定義：

- 服務類型：Python Web Service。
- 服務名稱：`shiny-app-v3`（這是設定檔中的名稱，與儲存庫名稱不同）。
- Build command：`pip install -r requirements.txt`
- Start command：`python -m shiny run --host 0.0.0.0 --port $PORT app.py`

部署時需由平台提供 `PORT`。儲存庫未附正式服務網址；存在設定檔不代表已有運作中的服務。

## 安全性與目前限制

在接入真實醫療資料或對外部署前，至少需要評估：

- FHIR 請求使用 `verify=False`，停用 TLS 憑證驗證；不宜直接作為正式環境設定。
- `fhir` 與 `obs` 來自外部參數，未設允許清單；後端會對指定目的地送出請求及 token。應限制可存取的 FHIR 來源與 resource URL。
- token 雖放在 fragment，仍會由前端傳至 Shiny 後端；不是「token 不離開瀏覽器」的設計。請使用受信任的 HTTPS 部署，不分享含 token 的網址、截圖或紀錄。
- 請求未設定 timeout、HTTP 狀態檢查或完整例外處理；連線失敗、過期 token 或非 JSON 回應可能導致錯誤。
- JSON 展開區可能顯示病人個資；目前程式沒有另外實作應用層登入、角色控管或去識別化。
- 未校驗單位、時間與缺值，也沒有重新驗證風險表的適用性。
- 目前沒有測試套件、完整環境鎖定檔或臨床驗證資料。

請先在測試環境使用合成或適當去識別化資料，確認欄位語意與輸入輸出，再依機構規範處理正式串接。

## 作者標示與授權

介面保留以下標示：

- Produced by Dr. Chin-Chieh Wu
- UI enhance and implement in SMART on FHIR by lenkun25369-ui

本次檢視時儲存庫沒有 LICENSE 檔；公開程式碼不等於已授予開源再利用權利。如需再散布或商業使用，請向權利人確認。

## 文件驗證範圍

本 README 依儲存庫的 `app.py`、`requirements.txt` 與 `render.yaml` 撰寫，並完成 Python 語法靜態解析；尚未執行相依套件安裝、UI 操作、FHIR 連線或 Render 部署測試。

