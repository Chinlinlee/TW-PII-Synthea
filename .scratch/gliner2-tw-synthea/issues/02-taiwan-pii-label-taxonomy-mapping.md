# 台灣 PII 實體與 GLiNER2 標籤映射體系設計
Type: prototype
Status: open
Blocked by: none

## Question

如何具體定義台灣個人資料實體（包含身分證字號、健保卡號、統一編號、車牌、護照號碼、駕照、LINE ID、PTT 帳號、戶號、醫事人員字號、軍人證號、民國年紀年、台灣各區市話、台灣郵遞區號地址）與 GLiNER2 原生 42 類標籤的映射表？
特別需要決策：
1. 哪些台灣實體直接映射至 GLiNER2 42 標籤（如：身分證 ➜ `national_id_number`、統編 ➜ `tax_id`、姓名 ➜ `person`、住址 ➜ `address`）？
2. 哪些實體必須新增台灣在地專有標籤（如：健保卡 `tw_nhi_card`、LINE ID `tw_line_id`、車牌 `license_plate`）？
3. 標籤名稱的英文規範與 GLiNER2 Inference Prompt 的對應文字（Promptable schema description）為何？產出可執行的 `schema.json` 與對應規格原型。
