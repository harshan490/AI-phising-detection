import hashlib
import re
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses, parseaddr
from typing import Any, Dict, List

from bs4 import BeautifulSoup

URL_RE = re.compile(r"https?://[^\s<>\"'()\[\]{}]+", re.IGNORECASE)
AUTH_RE = re.compile(r"\b(spf|dkim|dmarc)\s*=\s*([a-z]+)", re.IGNORECASE)


def _clean_url(u: str) -> str:
    return u.rstrip(".,;:!?'\"")


def html_to_text(html: str) -> str:
    if not html:
        return ""
    return BeautifulSoup(html, "lxml").get_text(" ", strip=True)


def domain_of_address(value: str) -> str:
    addr = parseaddr(value or "")[1]
    return addr.rsplit("@", 1)[-1].lower().strip(" >.") if "@" in addr else ""


class EmailParserService:
    def parse_eml(self, raw_bytes: bytes) -> Dict[str, Any]:
        msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)
        body = self._extract_body(msg)
        body["html_text"] = html_to_text(body["html"])
        links = self._extract_links(body["html"])
        urls = set(_clean_url(u) for u in URL_RE.findall(body["plain"] + " " + body["html_text"]))
        urls.update(href for _, href in links)
        return {
            "headers": self._extract_headers(msg),
            "body": body,
            "links": [{"text": t, "href": h} for t, h in links],
            "attachments": self._extract_attachments(msg),
            "urls": sorted(urls),
        }

    def _extract_headers(self, msg) -> Dict[str, Any]:
        def h(name):
            return str(msg.get(name, "") or "")

        auth = " ; ".join(str(v) for v in msg.get_all("Authentication-Results", []) or [])
        headers = {
            "sender": h("From"),
            "sender_name": parseaddr(h("From"))[0],
            "sender_domain": domain_of_address(h("From")),
            "receiver": h("To"),
            "subject": h("Subject"),
            "message_id": h("Message-ID"),
            "return_path": h("Return-Path"),
            "reply_to": h("Reply-To"),
            "date": h("Date"),
            "received": [str(v) for v in msg.get_all("Received", []) or []],
            "authentication_results": auth,
        }
        found = {}
        for mech, result in AUTH_RE.findall(auth):
            found.setdefault(mech.lower(), result.lower())  # first (outermost) result wins
        for mech in ("spf", "dkim", "dmarc"):
            headers[mech] = found.get(mech, "none")
        headers["reply_to_domains"] = [a.rsplit("@", 1)[-1].lower()
                                       for _, a in getaddresses([headers["reply_to"]]) if "@" in a]
        headers["return_path_domain"] = domain_of_address(headers["return_path"])
        return headers

    def _extract_body(self, msg) -> Dict[str, str]:
        body = {"plain": "", "html": ""}
        parts = msg.walk() if msg.is_multipart() else [msg]
        for part in parts:
            if part.is_multipart() or part.get_content_disposition() == "attachment":
                continue
            ctype = part.get_content_type()
            if ctype not in ("text/plain", "text/html"):
                continue
            try:
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                try:
                    text = payload.decode(charset, errors="ignore")
                except LookupError:
                    text = payload.decode("utf-8", errors="ignore")
            except Exception:
                continue
            body["plain" if ctype == "text/plain" else "html"] += text
        return body

    def _extract_links(self, html: str) -> List[tuple]:
        if not html:
            return []
        soup = BeautifulSoup(html, "lxml")
        links = []
        for a in soup.find_all("a", href=True):
            href = _clean_url(a["href"].strip())
            if href.lower().startswith(("http://", "https://")):
                links.append((a.get_text(" ", strip=True), href))
        return links

    def _extract_attachments(self, msg) -> List[Dict[str, Any]]:
        attachments = []
        for part in msg.walk():
            filename = part.get_filename()
            if part.get_content_disposition() == "attachment" or (filename and not part.is_multipart()):
                data = part.get_payload(decode=True) or b""
                attachments.append({
                    "filename": filename or "(unnamed)",
                    "content_type": part.get_content_type(),
                    "size": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                })
        return attachments

    @staticmethod
    def model_text(parsed: Dict[str, Any]) -> str:
        """Subject + plain body; add HTML-as-text when the plain part is missing/short."""
        plain = parsed["body"]["plain"].strip()
        text = parsed["headers"]["subject"] + "\n" + plain
        if len(plain) < 200:
            text += "\n" + parsed["body"].get("html_text", "")
        return text


email_parser = EmailParserService()
