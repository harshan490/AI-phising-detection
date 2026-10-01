from app.services import heuristics as H


def hdr(**kw):
    base = {"sender_name": "", "sender_domain": "example.com", "reply_to_domains": [],
            "return_path_domain": "", "spf": "pass", "dkim": "pass", "dmarc": "pass"}
    base.update(kw)
    return base


def by_id(checks, id_):
    return next(c for c in checks if c["id"] == id_)


def test_check_shape():
    c = H.check_keywords("hello")
    assert set(c) == {"id", "name", "category", "triggered", "severity", "evidence"}


def test_link_mismatch():
    assert H.check_link_mismatch([{"text": "www.paypal.com", "href": "http://evil.example/x"}])["triggered"]
    assert not H.check_link_mismatch([{"text": "paypal.com", "href": "https://www.paypal.com/x"}])["triggered"]
    assert not H.check_link_mismatch([{"text": "Click here", "href": "http://evil.example/x"}])["triggered"]
    # same brand, different official domain
    assert not H.check_link_mismatch([{"text": "dis.gd", "href": "https://discord.com/x"}])["triggered"]
    # ESP click-tracking redirect is reported in evidence but not counted
    c = H.check_link_mismatch([{"text": "shop.com", "href": "https://u1.ct.sendgrid.net/ls/click?x"}])
    assert not c["triggered"] and "sendgrid.net" in c["evidence"]


def test_reply_and_return_path():
    out = H.check_reply_return(hdr(sender_domain="bank.com", reply_to_domains=["gmail.com"],
                                   return_path_domain="mailer.net"))
    assert by_id(out, "reply_to_mismatch")["triggered"]
    assert by_id(out, "return_path_mismatch")["triggered"]
    out = H.check_reply_return(hdr(sender_domain="mail.bank.com", reply_to_domains=["bank.com"]))
    assert not by_id(out, "reply_to_mismatch")["triggered"]


def test_brand_display_mismatch():
    assert H.check_brand_display(hdr(sender_name="PayPal Support", sender_domain="secure-mail.ru"))["triggered"]
    assert not H.check_brand_display(hdr(sender_name="PayPal", sender_domain="mail.paypal.com"))["triggered"]
    assert not H.check_brand_display(hdr(sender_name="Discord", sender_domain="discord.com"))["triggered"]


def test_lookalike_domains():
    assert H.lookalike_reason("paypa1.com")
    assert H.lookalike_reason("micros0ft.com")
    assert H.lookalike_reason("xn--pypal-4ve.com")
    assert H.lookalike_reason("paypal-update-security.com")
    assert H.lookalike_reason("paypal.com") is None
    assert H.lookalike_reason("www.paypal.com") is None
    assert H.lookalike_reason("github.com") is None


def test_url_structure():
    checks = H.check_url_structure([
        "http://192.168.1.10/login", "https://bit.ly/abc", "http://user@evil.com/",
        "http://a.b.c.d.e.f.example.com/", "http://prize.xyz/claim",
    ])
    for id_ in ("ip_url", "url_shortener", "at_in_url", "many_subdomains", "suspicious_tld"):
        assert by_id(checks, id_)["triggered"], id_
    clean = H.check_url_structure(["https://www.wikipedia.org/wiki/Email"])
    assert not any(c["triggered"] for c in clean)


def test_attachments():
    out = H.check_attachments([{"filename": "invoice.pdf.exe"}, {"filename": "page.html"}])
    assert by_id(out, "risky_attachment")["triggered"]
    assert by_id(out, "double_extension")["triggered"]
    out = H.check_attachments([{"filename": "report.pdf"}])
    assert not any(c["triggered"] for c in out)


def test_auth():
    out = H.check_auth(hdr(spf="fail", dkim="none", dmarc="pass"))
    assert by_id(out, "spf_result")["severity"] == 1.0
    assert by_id(out, "dkim_result")["severity"] == 0.4
    assert not by_id(out, "dmarc_result")["triggered"]


def test_keywords():
    assert H.check_keywords("Please verify your password")["triggered"]
    assert not H.check_keywords("Lunch on Friday?")["triggered"]
