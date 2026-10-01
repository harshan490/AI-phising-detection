"""Rule-based phishing checks (local heuristics, no network).

Every check returns {id, name, category, triggered, severity (0-1), evidence}.
category is one of: url, sender, auth, attachment - used by risk.py.
"""
import ipaddress
import re
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

BRANDS: Dict[str, List[str]] = {
    "paypal": ["paypal.com"],
    "microsoft": ["microsoft.com", "outlook.com", "live.com", "office.com", "office365.com"],
    "apple": ["apple.com", "icloud.com"],
    "amazon": ["amazon.com", "amazon.in", "amazon.co.uk"],
    "google": ["google.com", "gmail.com", "youtube.com"],
    "netflix": ["netflix.com"],
    "bank": [],  # generic word: matched against "bank" in the sender domain
    "sbi": ["sbi.co.in", "onlinesbi.sbi", "sbi.bank.in"],
    "hdfc": ["hdfcbank.com", "hdfc.com"],
    "icici": ["icicibank.com"],
    "discord": ["discord.com", "discordapp.com", "discord.gg", "dis.gd"],
    "instagram": ["instagram.com"],
    "facebook": ["facebook.com", "facebookmail.com", "fb.com", "meta.com"],
    "dhl": ["dhl.com"],
    "fedex": ["fedex.com"],
}
OFFICIAL_DOMAINS = {d for ds in BRANDS.values() for d in ds}
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly"}
# Email-service-provider click-tracking domains (link targets are redirects).
TRACKING_DOMAINS = {"sendgrid.net", "list-manage.com", "mandrillapp.com", "mailgun.org", "mcsv.net",
                    "rs6.net", "sparkpostmail.com", "hubspotlinks.com", "exacttarget.com", "mailchimp.com"}
SUSPICIOUS_TLDS ={"zip", "top", "xyz", "tk", "ml", "ga", "cf", "gq", "click"}
RISKY_EXT = {"exe", "scr", "js", "vbs", "bat", "html", "htm", "iso", "img", "docm", "xlsm", "pptm"}
DECOY_EXT = {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "jpg", "jpeg", "png", "csv", "rtf"}
KEYWORDS = ["verify", "suspended", "urgent", "password", "login", "confirm your account",
            "wire", "gift card"]
SECOND_LEVEL = {"co", "com", "org", "net", "ac", "gov", "edu", "bank"}
DOMAIN_RE = re.compile(r"^(?:https?://)?(?:www\.)?([a-z0-9-]+(?:\.[a-z0-9-]+)+)(?:[/:?#]|$)", re.I)


def check(id_: str, name: str, category: str, triggered: bool, severity: float, evidence: str):
    return {"id": id_, "name": name, "category": category, "triggered": bool(triggered),
            "severity": round(severity if triggered else 0.0, 2), "evidence": evidence}


def host_of(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower().rstrip(".")
    except ValueError:
        return ""


def registrable(host: str) -> str:
    """Rough eTLD+1 (no public-suffix list): example.co.uk -> example.co.uk, a.b.com -> b.com."""
    labels = [l for l in host.lower().strip(".").split(".") if l]
    if len(labels) <= 2:
        return ".".join(labels)
    if labels[-2] in SECOND_LEVEL and len(labels[-1]) == 2:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def same_brand(a: str, b: str) -> bool:
    return any(a in ds and b in ds for ds in BRANDS.values())


def is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host.strip("[]"))
        return True
    except ValueError:
        return False


def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def lookalike_reason(domain: str) -> Optional[str]:
    """Why `domain` imitates a known brand, or None."""
    if not domain:
        return None
    if "xn--" in domain:
        return f"{domain} uses punycode (possible homoglyph domain)"
    reg = registrable(domain)
    if reg in OFFICIAL_DOMAINS or any(domain.endswith("." + d) for d in OFFICIAL_DOMAINS):
        return None
    label = reg.split(".")[0]
    for brand, real in BRANDS.items():
        for rd in real:
            rlabel = rd.split(".")[0]
            d = levenshtein(label, rlabel)
            if 0 < d <= 2 and len(rlabel) >= 5:
                return f"{reg} is {d} edit(s) away from {rd}"
        if brand != "bank" and len(brand) >= 4 and brand in label:
            return f"{reg} contains brand '{brand}' but is not an official {brand} domain"
    return None


# ---------------------------------------------------------------- URL checks
def check_link_mismatch(links: List[Dict[str, str]]):
    hits, tracked = [], set()
    for link in links:
        m = DOMAIN_RE.match(link.get("text", "").strip())
        if not m or "." not in m.group(1) or m.group(1).split(".")[-1].isdigit():
            continue
        shown, actual = registrable(m.group(1)), registrable(host_of(link["href"]))
        if not actual or shown == actual or same_brand(shown, actual):
            continue
        if actual in TRACKING_DOMAINS:
            tracked.add(actual)  # ESP click-tracking redirect: real target unknown, not counted
            continue
        hits.append(f"text '{m.group(1)}' -> {actual}")
    hits = list(dict.fromkeys(hits))
    note = f" (ignored click-tracking redirects via {', '.join(sorted(tracked))})" if tracked else ""
    return check("link_text_mismatch", "Link text domain differs from real link target", "url",
                 bool(hits), 0.8, ("; ".join(hits[:3]) or "visible link domains match their targets") + note)


def check_url_structure(urls: Iterable[str]) -> List[Dict[str, Any]]:
    ip, short, at, subs, tld, look = [], [], [], [], [], []
    for u in urls:
        host = host_of(u)
        if not host:
            continue
        if is_ip(host):
            ip.append(host)
        if registrable(host) in SHORTENERS or host in SHORTENERS:
            short.append(host)
        if "@" in (urlparse(u).netloc or ""):
            at.append(u[:80])
        if len(host.split(".")) - len(registrable(host).split(".")) > 4:
            subs.append(host)
        if host.rsplit(".", 1)[-1] in SUSPICIOUS_TLDS:
            tld.append(host)
        reason = lookalike_reason(host)
        if reason:
            look.append(reason)

    def ev(items, none):
        items = sorted(set(items))
        return ", ".join(items[:3]) + (f" (+{len(items) - 3} more)" if len(items) > 3 else "") if items else none

    return [
        check("ip_url", "URL uses a raw IP address", "url", ip, 0.9, ev(ip, "no IP-address URLs")),
        check("url_shortener", "URL shortener used", "url", short, 0.5, ev(short, "no shorteners")),
        check("at_in_url", "'@' in URL authority", "url", at, 0.7, ev(at, "none")),
        check("many_subdomains", "More than 4 subdomains", "url", subs, 0.5, ev(subs, "none")),
        check("suspicious_tld", "Suspicious top-level domain", "url", tld, 0.6, ev(tld, "none")),
        check("lookalike_url_domain", "Look-alike / punycode domain in URL", "url", look, 1.0,
              ev(look, "no brand look-alikes")),
    ]


# ------------------------------------------------------------- sender checks
def check_reply_return(headers: Dict[str, Any]):
    frm = registrable(headers.get("sender_domain", ""))
    out = []
    reply = [registrable(d) for d in headers.get("reply_to_domains", [])]
    bad_reply = [d for d in reply if frm and d != frm]
    out.append(check("reply_to_mismatch", "Reply-To domain differs from From", "sender", bad_reply, 0.6,
                     f"From {frm}, Reply-To {', '.join(bad_reply)}" if bad_reply else "Reply-To absent or matches"))
    rp = registrable(headers.get("return_path_domain", ""))
    bad_rp = bool(frm and rp and rp != frm)
    # Low severity: bulk senders legitimately use a separate bounce domain.
    out.append(check("return_path_mismatch", "Return-Path domain differs from From", "sender", bad_rp, 0.3,
                     f"From {frm}, Return-Path {rp}" if bad_rp else "Return-Path absent or matches"))
    return out


def check_brand_display(headers: Dict[str, Any]):
    name = (headers.get("sender_name") or "").lower()
    dom = (headers.get("sender_domain") or "").lower()
    for brand, real in BRANDS.items():
        if not re.search(rf"\b{re.escape(brand)}\b", name):
            continue
        ok = ("bank" in dom) if brand == "bank" else any(dom == d or dom.endswith("." + d) for d in real)
        if not ok:
            return check("brand_display_mismatch", "Display name impersonates a brand", "sender", True, 0.9,
                         f"display name '{headers.get('sender_name')}' but sent from {dom or 'unknown domain'}")
    return check("brand_display_mismatch", "Display name impersonates a brand", "sender", False, 0.9,
                 "no brand mismatch in display name")


def check_sender_lookalike(headers: Dict[str, Any]):
    reason = lookalike_reason(headers.get("sender_domain", ""))
    return check("lookalike_sender_domain", "Look-alike / punycode sender domain", "sender", reason, 1.0,
                 reason or "sender domain is not a brand look-alike")


def check_keywords(text: str):
    low = text.lower()
    hits = [k for k in KEYWORDS if re.search(rf"\b{re.escape(k)}\b", low)]
    return check("urgency_keywords", "Urgency / credential keywords", "sender", hits, 0.3,
                 ", ".join(hits) or "none")


# --------------------------------------------------------------- auth checks
def check_auth(headers: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for mech in ("spf", "dkim", "dmarc"):
        res = headers.get(mech, "none")
        if res == "pass":
            sev, trig = 0.0, False
        elif res in ("none", "neutral"):
            sev, trig = 0.4, True
        else:  # fail, softfail, permerror, temperror ...
            sev, trig = 1.0, True
        out.append(check(f"{mech}_result", f"{mech.upper()} not passing", "auth", trig, sev,
                         f"{mech.upper()}={res}"))
    return out


# --------------------------------------------------------- attachment checks
def check_attachments(attachments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    risky, double = [], []
    for a in attachments:
        fn = (a.get("filename") or "").lower()
        parts = fn.split(".")
        if len(parts) >= 2 and parts[-1] in RISKY_EXT:
            risky.append(fn)
        if len(parts) >= 3 and parts[-2] in DECOY_EXT and parts[-1] != parts[-2]:
            double.append(fn)
    return [
        check("risky_attachment", "Risky attachment type", "attachment", risky, 0.9,
              ", ".join(risky) or "no risky attachment types"),
        check("double_extension", "Double file extension", "attachment", double, 1.0,
              ", ".join(double) or "no double extensions"),
    ]


def run_all(parsed: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
    h = parsed["headers"]
    return [
        check_link_mismatch(parsed.get("links", [])),
        *check_url_structure(parsed.get("urls", [])),
        *check_reply_return(h),
        check_brand_display(h),
        check_sender_lookalike(h),
        check_keywords(text),
        *check_auth(h),
        *check_attachments(parsed.get("attachments", [])),
    ]
