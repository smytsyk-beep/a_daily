# tests/test_pdf_daily_stub.py

from datetime import date

from app.pdf_daily import build_daily_digest_pdf


def test_build_daily_digest_pdf_stub_basic():
    title = "Today's focus: Balance"
    body = "Today is a good day to slow down and focus on essentials."
    affirmation = "I move at my own healthy pace."

    pdf_bytes = build_daily_digest_pdf(
        title=title,
        body=body,
        affirmation=affirmation,
        locale="en",
    )

    # 1) Должны получить bytes, не пустые
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 20

    text = pdf_bytes.decode("utf-8")

    # 2) В текстовой версии должны присутствовать ключевые части
    assert "AstroDaily — Daily Digest" in text
    assert "Locale: en" in text
    assert title in text
    assert body in text
    assert affirmation in text
