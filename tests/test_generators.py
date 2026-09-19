"""
Comprehensive Unit Tests for Taiwan Synthetic PII Generators and Offset Engine.
Validates algorithmic correctness, checksums, taxonomy coverage, and offset preservation.
"""

import re
import pytest

from pii_synthea.generators import (
    FAMOUS_TAIWAN_COMPANIES,
    TAIWAN_ADMIN_DIVISIONS,
    Span,
    SpanReplacer,
    SynthesisResult,
    TaiwanPIIGenerator,
    TemplateEngine,
    calculate_id_check_digit,
    generate_address,
    generate_bank_account,
    generate_card_cvv,
    generate_date_of_birth,
    generate_drivers_license_number,
    generate_email,
    generate_household_no,
    generate_landline_number,
    generate_license_plate,
    generate_line_id,
    generate_medical_license,
    generate_military_id,
    generate_mobile_number,
    generate_national_id,
    generate_nhi_card,
    generate_passport_number,
    generate_payment_card,
    generate_person_name,
    generate_phone_number,
    generate_postal_code,
    generate_ptt_id,
    generate_secret,
    generate_tax_id,
    validate_bank_account,
    validate_card_cvv,
    validate_credit_card,
    validate_email,
    validate_household_no,
    validate_license_plate,
    validate_line_id,
    validate_medical_license,
    validate_military_id,
    validate_national_id,
    validate_nhi_card,
    validate_passport_number,
    validate_phone_number,
    validate_postal_code,
    validate_ptt_id,
    validate_tax_id,
)
from pii_synthea.taxonomy import CANONICAL_TAXONOMY


# ── 1. National ID & ARC Tests ────────────────────────────────────────────────


def test_national_id_known_cases():
    # Famous valid test IDs
    assert validate_national_id("A123456789") is True
    # Modify check digit to create invalid ID
    assert validate_national_id("A123456780") is False
    assert validate_national_id("A123456788") is False
    # Invalid length or non-letter prefix
    assert validate_national_id("1123456789") is False
    assert validate_national_id("A12345678") is False
    assert validate_national_id("A1234567890") is False


def test_national_id_generation_batches():
    # 50 Citizen Male & Female IDs
    for _ in range(50):
        cid_m = generate_national_id(gender=1, id_type="citizen")
        assert cid_m[1] == "1"
        assert validate_national_id(cid_m) is True

        cid_f = generate_national_id(gender=2, id_type="citizen")
        assert cid_f[1] == "2"
        assert validate_national_id(cid_f) is True

    # 30 New ARC IDs
    for _ in range(30):
        arc_m = generate_national_id(gender=8, id_type="new_arc")
        assert arc_m[1] == "8"
        assert validate_national_id(arc_m) is True

        arc_f = generate_national_id(gender=9, id_type="new_arc")
        assert arc_f[1] == "9"
        assert validate_national_id(arc_f) is True

    # 30 Old ARC IDs
    for _ in range(30):
        old_arc = generate_national_id(id_type="old_arc")
        assert old_arc[1] in ("A", "B", "C", "D")
        assert validate_national_id(old_arc) is True


def test_household_number():
    assert validate_household_no("A1234567") is True
    assert validate_household_no("F7654321") is True
    assert validate_household_no("12345678") is False
    assert validate_household_no("AB123456") is False

    for _ in range(30):
        hno = generate_household_no()
        assert validate_household_no(hno) is True


# ── 2. Unified Business Tax ID (統編) Tests ────────────────────────────────────


def test_tax_id_famous_companies():
    for name, ubn in FAMOUS_TAIWAN_COMPANIES.items():
        assert validate_tax_id(ubn) is True, f"Failed for {name}: {ubn}"


def test_tax_id_generator_and_validator():
    # 100 generated Tax IDs must all pass validation
    for _ in range(100):
        ubn = generate_tax_id()
        assert len(ubn) == 8
        assert validate_tax_id(ubn) is True

    # Test edge case: 7th digit = 7
    for _ in range(30):
        ubn_7 = generate_tax_id(force_seventh_digit_seven=True)
        assert ubn_7[6] == "7"
        assert validate_tax_id(ubn_7) is True

    # Test invalid tax IDs
    assert validate_tax_id("12345670") is False  # bad checksum
    assert validate_tax_id("1234567") is False   # length 7
    assert validate_tax_id("123456789") is False # length 9
    assert validate_tax_id("abcdefgh") is False


# ── 3. Address & Postal Code Tests ────────────────────────────────────────────


def test_postal_code_generator_and_validator():
    for _ in range(50):
        p3 = generate_postal_code(format_type="3")
        assert validate_postal_code(p3) is True
        assert len(p3) == 3

        p32 = generate_postal_code(format_type="3+2")
        assert validate_postal_code(p32) is True

        p33 = generate_postal_code(format_type="3+3")
        assert validate_postal_code(p33) is True

    # District-specific postal code check
    code_daan = generate_postal_code(city="台北市", district="大安區", format_type="3")
    assert code_daan == "106"

    code_banqiao = generate_postal_code(city="新北市", district="板橋區", format_type="3")
    assert code_banqiao == "220"


def test_address_generator():
    for _ in range(50):
        addr = generate_address(include_postal_code=False)
        assert addr.city in TAIWAN_ADMIN_DIVISIONS
        assert addr.district in TAIWAN_ADMIN_DIVISIONS[addr.city]
        assert addr.city in addr.full_address
        assert addr.district in addr.full_address
        assert "號" in addr.full_address

    # Address with postal code
    addr_with_code = generate_address(city="台北市", district="大安區", include_postal_code=True)
    assert addr_with_code.full_address.startswith("106")


# ── 4. Person Names Tests ─────────────────────────────────────────────────────


def test_person_name_generator():
    # Chinese standard
    for _ in range(30):
        name = generate_person_name(style="zh")
        assert 2 <= len(name) <= 4

    # Compound surname
    for _ in range(15):
        cname = generate_person_name(style="compound")
        assert len(cname) >= 3

    # Indigenous
    for _ in range(15):
        iname = generate_person_name(style="indigenous")
        assert len(iname) >= 2

    # Romanized
    for _ in range(15):
        rname = generate_person_name(style="romanized")
        assert " " in rname


# ── 5. Phone Numbers Tests ────────────────────────────────────────────────────


def test_mobile_number():
    for _ in range(50):
        dashed = generate_mobile_number(format_style="dashed")
        assert validate_phone_number(dashed) is True

        compact = generate_mobile_number(format_style="compact")
        assert validate_phone_number(compact) is True

        intl = generate_mobile_number(format_style="intl_dashed")
        assert validate_phone_number(intl) is True


def test_landline_number():
    for area in ["02", "04", "07", "03"]:
        for _ in range(10):
            phone = generate_landline_number(area_code=area, format_style="dashed")
            assert validate_phone_number(phone) is True

            paren = generate_landline_number(area_code=area, format_style="parentheses")
            assert validate_phone_number(paren) is True


def test_unified_phone():
    for _ in range(40):
        p = generate_phone_number()
        assert validate_phone_number(p) is True


# ── 6. Financial PII Tests ────────────────────────────────────────────────────


def test_payment_cards_luhn():
    for brand in ["visa", "mastercard", "jcb"]:
        for _ in range(20):
            card = generate_payment_card(card_brand=brand, format_style="dashed")
            assert validate_credit_card(card) is True

            card_compact = generate_payment_card(card_brand=brand, format_style="compact")
            assert validate_credit_card(card_compact) is True

    # Bad Luhn card
    assert validate_credit_card("4563-1234-5678-9011") is False


def test_card_cvv():
    for _ in range(20):
        cvv = generate_card_cvv(digits=3)
        assert validate_card_cvv(cvv) is True
        assert len(cvv) == 3


def test_bank_account():
    for _ in range(30):
        acc = generate_bank_account()
        assert validate_bank_account(acc) is True


# ── 7. Misc PII Tests ─────────────────────────────────────────────────────────


def test_nhi_card():
    for _ in range(20):
        nhi = generate_nhi_card(format_style="compact")
        assert validate_nhi_card(nhi) is True
        assert len(nhi) == 12


def test_license_plates():
    for ptype in ["new_car", "old_car", "motorcycle"]:
        for _ in range(15):
            plate = generate_license_plate(plate_type=ptype)
            assert validate_license_plate(plate) is True


def test_passport_and_driver_license():
    for _ in range(20):
        pass_num = generate_passport_number()
        assert validate_passport_number(pass_num) is True
        assert len(pass_num) == 9

    for _ in range(10):
        dl = generate_drivers_license_number(style="national_id")
        assert validate_national_id(dl) is True


def test_line_and_ptt_id():
    for _ in range(20):
        lid = generate_line_id()
        assert validate_line_id(lid) is True

        pid = generate_ptt_id()
        assert validate_ptt_id(pid) is True


def test_medical_and_military_licenses():
    for _ in range(15):
        med = generate_medical_license()
        assert validate_medical_license(med) is True

        mil = generate_military_id()
        assert validate_military_id(mil) is True


def test_email_and_secrets():
    for _ in range(20):
        email = generate_email()
        assert validate_email(email) is True

        secret = generate_secret()
        assert len(secret) >= 6


# ── 8. Master Hub & All 21 Canonical Entities ─────────────────────────────────


def test_master_hub_covers_all_21_canonical_labels():
    gen = TaiwanPIIGenerator(seed=42)
    all_entities = gen.generate_all()
    assert len(all_entities) == 21

    for canonical_id in CANONICAL_TAXONOMY.keys():
        assert canonical_id in all_entities
        val = all_entities[canonical_id]
        assert isinstance(val, str)
        assert len(val) > 0

    # Test individual generate
    for canonical_id in CANONICAL_TAXONOMY.keys():
        val = gen.generate(canonical_id)
        assert isinstance(val, str)
        assert len(val) > 0


def test_master_hub_reproducibility():
    gen1 = TaiwanPIIGenerator(seed=12345)
    gen2 = TaiwanPIIGenerator(seed=12345)
    assert gen1.generate_all() == gen2.generate_all()


# ── 9. Template Engine & Offset Preservation Tests ────────────────────────────


def test_template_engine_exact_offsets():
    engine = TemplateEngine(seed=999)
    template = (
        "敬啟者 {{person:1}}（身分證字號：{{national_id_number:1}}）：\n"
        "您所登記的通訊地址為 {{address:1}}，所屬公司統一編號為 {{tax_id:1}}。\n"
        "我們已將驗證碼 {{secret:1}} 寄送至您的電子郵件 {{email:1}}，"
        "如有疑問請致電 {{phone_number:1}} 與我們聯繫。簽收人：{{person:1}}。"
    )

    result = engine.render(template)
    assert result.validate() is True

    # 100% exact character slice assertion
    for span in result.spans:
        assert result.text[span.start:span.end] == span.text

    # Check indexed binding reuse (person:1 appears twice with exact same name)
    person_spans = [s for s in result.spans if s.canonical_id == "person"]
    assert len(person_spans) == 2
    assert person_spans[0].text == person_spans[1].text
    assert result.text[person_spans[0].start:person_spans[0].end] == person_spans[0].text
    assert result.text[person_spans[1].start:person_spans[1].end] == person_spans[1].text

    # Check GLiNER2 export format
    gliner_item = result.to_gliner2_format()
    assert gliner_item["text"] == result.text
    assert len(gliner_item["spans"]) == len(result.spans)
    for s in gliner_item["spans"]:
        assert gliner_item["text"][s["start"]:s["end"]] == s["text"]


def test_template_engine_tag_format():
    engine = TemplateEngine(seed=777)
    template = "客戶姓名：<person>，車牌號碼：<license_plate>，健保卡號：<tw_nhi_card>。"
    result = engine.render(template)
    assert result.validate() is True
    assert len(result.spans) == 3
    for s in result.spans:
        assert result.text[s.start:s.end] == s.text


def test_synthesis_result_validation_detects_errors():
    # Test text mismatch raises ValueError
    bad_result = SynthesisResult(
        text="台北市大安區",
        spans=[Span(start=0, end=3, label="address", text="新北市")],
    )
    with pytest.raises(ValueError, match="Span text mismatch"):
        bad_result.validate()

    # Test out of bounds raises ValueError
    oob_result = SynthesisResult(
        text="你好",
        spans=[Span(start=0, end=10, label="person", text="你好")],
    )
    with pytest.raises(ValueError, match="Span boundary invalid"):
        oob_result.validate()

    # Test overlapping spans raise ValueError
    overlap_result = SynthesisResult(
        text="台北市中正區忠孝東路",
        spans=[
            Span(start=0, end=6, label="address", text="台北市中正區"),
            Span(start=3, end=10, label="address", text="中正區忠孝東路"),
        ],
    )
    with pytest.raises(ValueError, match="Overlapping spans detected"):
        overlap_result.validate()


# ── 10. Span Replacer Tests ───────────────────────────────────────────────────


def test_span_replacer_shifts_offsets():
    orig_text = "用戶 陳大明（身分證 A123456789）住在 台北市中正區。"
    spans = [
        Span(start=3, end=6, label="person", text="陳大明"),
        Span(start=11, end=21, label="national_id_number", text="A123456789"),
        Span(start=25, end=31, label="address", text="台北市中正區"),
    ]
    orig_res = SynthesisResult(text=orig_text, spans=spans)
    assert orig_res.validate() is True

    # Replace "陳大明" (len 3) with "歐陽小華" (len 4) -> delta +1
    # Replace "台北市中正區" (len 6) with "台中市西屯區台灣大道三段99號" (len 16) -> delta +10
    replacements = {
        0: "歐陽小華",
        2: "台中市西屯區台灣大道三段99號",
    }
    new_res = SpanReplacer.replace_spans(orig_text, spans, replacements)
    assert new_res.validate() is True

    # Verify that all updated spans match the new text slices exactly
    for s in new_res.spans:
        assert new_res.text[s.start:s.end] == s.text

    assert new_res.spans[0].text == "歐陽小華"
    # The middle span "A123456789" was shifted by +1
    assert new_res.spans[1].start == 12
    assert new_res.spans[1].end == 22
    assert new_res.spans[1].text == "A123456789"
    assert new_res.spans[2].text == "台中市西屯區台灣大道三段99號"
