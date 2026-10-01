"""Create privacy-redacted copies of the two real sample emails for the public repo.

Usage (from repo root): python backend/tests/fixtures/redact_samples.py <extra usernames to scrub...>
Replaces the recipient's address/usernames, strips tracking tokens from URL query
strings and drops headers that carry per-recipient data. Everything else (sender,
subject, body text, link domains, Authentication-Results) is kept so the analysis
still exercises the real content.
"""
import re
import sys
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCES = {
    "*$30,000,000 USD could be yours!.eml": "real_scam_lottery_redacted.eml",
    "Discord Password Changed.eml": "real_discord_password_changed_redacted.eml",
}
DROP = {"received", "arc-seal", "arc-message-signature", "arc-authentication-results", "dkim-signature",
        "x-google-smtp-source", "x-received", "x-gm-message-state", "list-unsubscribe",
        "list-unsubscribe-post", "x-feedback-id", "feedback-id", "x-sg-eid", "x-sg-id",
        "x-entity-id", "delivered-to", "x-original-to", "return-path"}
TOKEN_RE = re.compile(r"(?<![/:])/(?:u001\.)?[A-Za-z0-9_\-.~%=]{24,}")
URL_RE = re.compile(r"(https?://[^\s\"'<>?]+)\?[^\s\"'<>]*")


def redact_text(text: str, secrets) -> str:
    text = URL_RE.sub(r"\1?redacted=1", text)
    # per-recipient tracking tokens inside URL paths (e.g. sendgrid /ss/c/u001.xxxx)
    text = TOKEN_RE.sub("/redacted", text)
    for s in secrets:
        text = re.sub(re.escape(s), "student", text, flags=re.I)
    return text


def main():
    usernames = sys.argv[1:]  # extra identifiers to scrub (e.g. account usernames)
    for src, dst in SOURCES.items():
        msg = BytesParser(policy=policy.default).parsebytes(next(ROOT.glob(src)).read_bytes())
        to_addr = parseaddr(str(msg.get("To", "")))[1]
        local = to_addr.split("@")[0]
        secrets = [to_addr, local, *usernames]
        for name in list(msg.keys()):
            if name.lower() in DROP:
                del msg[name]
        for name, value in list(msg.items()):
            new = redact_text(str(value), secrets).replace("student@gmail.com", "student@example.com")
            if new != str(value):
                msg.replace_header(name, new)
        msg.replace_header("To", "student@example.com")
        for part in msg.walk():
            if part.get_content_maintype() == "text" and not part.is_multipart():
                body = redact_text(part.get_content(), secrets).replace("student@gmail.com", "student@example.com")
                part.set_content(body, subtype=part.get_content_subtype())
        (OUT / dst).write_bytes(msg.as_bytes(policy=policy.SMTP))
        print("wrote", dst)


if __name__ == "__main__":
    main()
