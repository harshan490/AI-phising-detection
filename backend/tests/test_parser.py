from app.services.email_parser import email_parser
from conftest import SCAM_EML


def test_parse_eml():
    mock_eml = b"""From: "Paypal Security" <security@paypal-update-security.com>
To: target@example.com
Subject: Urgent Action Required: Account Suspended
Date: Wed, 27 Jun 2026 12:00:00 +0000
Message-ID: <123456@paypal-update-security.com>
Content-Type: text/plain; charset="utf-8"
Authentication-Results: mx.example.com; spf=fail (sender IP is 1.2.3.4); dkim=fail; dmarc=fail

Dear User,
Your account has been suspended. Please visit http://paypal-update-security.com/login to restore access.
"""
    parsed = email_parser.parse_eml(mock_eml)
    h = parsed["headers"]
    assert h["sender_domain"] == "paypal-update-security.com"
    assert h["subject"] == "Urgent Action Required: Account Suspended"
    assert (h["spf"], h["dkim"], h["dmarc"]) == ("fail", "fail", "fail")
    assert "http://paypal-update-security.com/login" in parsed["urls"]


def test_html_only_email_gets_text():
    parsed = email_parser.parse_eml(SCAM_EML.read_bytes())
    assert parsed["body"]["plain"] == ""
    assert len(parsed["body"]["html_text"]) > 200
    assert len(email_parser.model_text(parsed)) > 200
