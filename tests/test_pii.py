from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in str(out)
    assert "REDACTED_EMAIL" in str(out)

def test_scrub_phone() -> None:
    out = scrub_text("Call me at 0901234567")
    assert "0901234567" not in str(out)
    assert "REDACTED_PHONE_VN" in str(out)

def test_scrub_cccd() -> None:
    out = scrub_text("CCCD: 012345678901")
    assert "012345678901" not in str(out)
    assert "REDACTED_CCCD" in str(out)

def test_scrub_passport() -> None:
    out = scrub_text("Passport: B1234567")
    assert "B1234567" not in str(out)
    assert "REDACTED_PASSPORT_VN" in str(out)

def test_scrub_tax_id() -> None:
    out = scrub_text("Tax ID: 0101234567")
    assert "0101234567" not in str(out)
    assert "REDACTED_TAX_ID_VN" in str(out)

def test_scrub_address_keywords() -> None:
    out = scrub_text("I live at Đường Lê Lợi, Quận 1, Thành phố Hồ Chí Minh")
    assert "Đường" not in str(out)
    assert "Quận" not in str(out)
    assert "Thành phố" not in str(out)
    assert "REDACTED_ADDRESS_VN" in str(out)

def test_scrub_ipv4() -> None:
    out = scrub_text("My IP is 192.168.1.1")
    assert "192.168.1.1" not in str(out)
    assert "REDACTED_IPV4" in str(out)
