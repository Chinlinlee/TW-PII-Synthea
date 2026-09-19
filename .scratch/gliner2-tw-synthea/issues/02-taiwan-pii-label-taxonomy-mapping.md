# 台灣 PII 實體與 GLiNER2 標籤映射體系設計
Type: prototype
Status: resolved
Blocked by: none

## Question

如何具體定義台灣個人資料實體（包含身分證字號、健保卡號、統一編號、車牌、護照號碼、駕照、LINE ID、PTT 帳號、戶號、醫事人員字號、軍人證號、民國年紀年、台灣各區市話、台灣郵遞區號地址）與 GLiNER2 原生 42 類標籤的映射表？
特別需要決策：
1. 哪些台灣實體直接映射至 GLiNER2 42 標籤（如：身分證 ➜ `national_id_number`、統編 ➜ `tax_id`、姓名 ➜ `person`、住址 ➜ `address`）？
2. 哪些實體必須新增台灣在地專有標籤（如：健保卡 `tw_nhi_card`、LINE ID `tw_line_id`、車牌 `license_plate`）？
3. 標籤名稱的英文規範與 GLiNER2 Inference Prompt 的對應文字（Promptable schema description）為何？產出可執行的 `schema.json` 與對應規格原型。

## Answer

已完成完整的 21 類台灣 PII 標籤體系設計、雙向映射表與可執行的原型規格：

1. **核心程式與規格資產**：
   - 映射與標籤類別程式：`src/pii_synthea/taxonomy.py`（提供 `TaxonomyMapper`、雙向轉換與查詢函式）。
   - 機器可讀規格：`schema.json`（包含 21 類實體之英繁對照 Prompt 描述、正則檢驗 pattern 與範例）。
   - 單元測試套件：`tests/test_taxonomy.py`（覆蓋率與正則皆通過測試，4 passed in 0.02s）。

2. **實體分類與映射決策**：
   - **標準 GLiNER2 原生映射（14 類）**：
     - 身分證字號 / 居留證 ➜ `national_id_number`
     - 統一編號 (統編) ➜ `tax_id`
     - 自然人姓名 ➜ `person`
     - 通訊/戶籍地址 ➜ `address`
     - 郵遞區號 ➜ `postal_code`
     - 手機與市話 ➜ `phone_number`
     - 電子信箱 ➜ `email`
     - 出生日期（民國年/西元年）➜ `date_of_birth`
     - 護照號碼 ➜ `passport_number`
     - 駕照號碼 ➜ `drivers_license_number`
     - 銀行帳號 ➜ `bank_account`
     - 信用卡號 ➜ `payment_card`
     - 信用卡背面末三碼 ➜ `card_cvv`
     - 密碼/金鑰/OTP ➜ `secret`
   - **台灣專屬在地擴充標籤（7 類）**：
     - 健保卡卡號 ➜ `tw_nhi_card`（通用 fallback: `government_id`）
     - 汽機車車牌 ➜ `license_plate`（通用 fallback: `license_number`）
     - LINE ID ➜ `tw_line_id`（通用 fallback: `username`）
     - PTT 帳號 ➜ `tw_ptt_id`（通用 fallback: `username`）
     - 戶口名簿戶號 ➜ `tw_household_no`（通用 fallback: `government_id`）
     - 醫事人員證照字號 ➜ `tw_medical_license`（通用 fallback: `license_number`）
     - 現役軍人證號 ➜ `tw_military_id`（通用 fallback: `government_id`）

3. **tw-PII-bench 雙向轉換**：
   - `tw_national_id` ⟷ `national_id_number`
   - `tw_company_id` ⟷ `tax_id`
   - `private_person` ⟷ `person`
   - `private_address` ⟷ `address`
   - `private_phone` ⟷ `phone_number`
   - `private_email` ⟷ `email`
   - `private_date` ⟷ `date_of_birth`
   - 其餘 OOD 標籤保持 1:1 映射，評測時可自動對齊。
