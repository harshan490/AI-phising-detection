"""End-to-end analysis of one .eml file: parse -> heuristics -> TI -> model -> risk -> persist."""
import ipaddress
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.scan import IOC, Scan
from app.services.ai_model import ai_model
from app.services.email_parser import email_parser
from app.services.heuristics import host_of, registrable, run_all
from app.services.risk import compute_risk
from app.services.threat_intel import LOCAL_LABEL, threat_intel

logger = logging.getLogger(__name__)
VERDICT_RANK = {"Safe": 0, "Suspicious": 1, "Phishing": 2}


def analyse(raw: bytes, db: Session) -> Dict[str, Any]:
    logs = ["[System] Scan started."]
    parsed = email_parser.parse_eml(raw)
    h = parsed["headers"]
    logs.append(f"[Parser] {len(parsed['urls'])} URLs, {len(parsed['attachments'])} attachments, "
                f"plain={len(parsed['body']['plain'])} chars, html={len(parsed['body']['html'])} chars.")
    logs.append(f"[Auth] Authentication-Results: SPF={h['spf'].upper()}, DKIM={h['dkim'].upper()}, "
                f"DMARC={h['dmarc'].upper()} (read from headers, not re-verified).")

    text = email_parser.model_text(parsed)
    checks = run_all(parsed, text)
    logs.append(f"[Heuristics] {sum(c['triggered'] for c in checks)}/{len(checks)} local checks triggered.")

    url_intel = [threat_intel.check_url(u) for u in parsed["urls"]]
    sender_host = h["sender_domain"]
    sender_blocked = bool(sender_host) and threat_intel.blocklisted(sender_host)
    blocklist_hit = sender_blocked or any(r["malicious"] for r in url_intel)
    domains = sorted({registrable(host_of(u)) for u in parsed["urls"] if host_of(u)})
    external = threat_intel.external_lookup(db, domains)
    if any(r.get("malicious") for r in external["results"]):
        blocklist_hit = True
    logs.append(f"[Threat Intel] {LOCAL_LABEL}: {'HIT' if blocklist_hit else 'no hits'}. "
                f"External: {external['status']}.")

    text_prob = ai_model.predict_proba(text)
    terms = ai_model.top_terms(text)
    logs.append(f"[AI Model] Text phishing probability {text_prob * 100:.1f}% (TF-IDF + Logistic Regression).")

    risk = compute_risk(text_prob, checks, blocklist_hit, terms)
    logs.append(f"[Risk] Score {risk['risk_score']}/100 -> {risk['verdict']}.")

    body = parsed.pop("body")
    result = {
        **risk,
        "prediction": risk["verdict"],
        "confidence": text_prob,
        "text_probability": text_prob,
        "xai_reasons": terms,
        "explanation_method": "top_terms (TF-IDF weight x LR coefficient)",
        "checks": checks,
        "headers": h,
        "urls": parsed["urls"],
        "links": parsed["links"][:50],
        "attachments": parsed["attachments"],
        "body_preview": (body["plain"] or body["html_text"])[:500],
        "threat_intel": {
            "source": LOCAL_LABEL,
            "sender_domain_blocklisted": sender_blocked,
            "url_results": url_intel,
            "external": external,
        },
        "model_version": ai_model.version,
        "logs": logs,
    }
    return result


def _upsert_ioc(db: Session, type_: str, value: str, verdict: str, now: datetime):
    if not value:
        return
    value = value[:2000]
    ioc = db.query(IOC).filter_by(type=type_, value=value).first()
    if ioc is None:
        ioc = IOC(type=type_, value=value, first_seen=now, hit_count=0, max_verdict=verdict)
        db.add(ioc)
    ioc.last_seen = now
    ioc.hit_count = (ioc.hit_count or 0) + 1
    if VERDICT_RANK.get(verdict, 0) > VERDICT_RANK.get(ioc.max_verdict, 0):
        ioc.max_verdict = verdict


def record_iocs(db: Session, result: Dict[str, Any], now: datetime):
    verdict = result["verdict"]
    domains, ips = set(), set()
    if result["headers"].get("sender_domain"):
        domains.add(result["headers"]["sender_domain"])
    for u in result["urls"]:
        host = host_of(u)
        try:
            ipaddress.ip_address(host.strip("[]"))
            ips.add(host)
        except ValueError:
            if host:
                domains.add(host)
        _upsert_ioc(db, "url", u, verdict, now)
    for d in domains:
        _upsert_ioc(db, "domain", d, verdict, now)
    for ip in ips:
        _upsert_ioc(db, "ip", ip, verdict, now)
    for a in result["attachments"]:
        _upsert_ioc(db, "sha256", a["sha256"], verdict, now)


def scan_and_store(raw: bytes, filename: str, user_id: int, db: Session) -> Scan:
    result = analyse(raw, db)
    now = datetime.now(timezone.utc)
    scan = Scan(id=str(uuid.uuid4()), user_id=user_id, filename=filename,
                subject=result["headers"]["subject"][:500], sender=result["headers"]["sender"][:500],
                verdict=result["verdict"], risk_score=result["risk_score"],
                result_json=json.dumps(result), created_at=now)
    db.add(scan)
    record_iocs(db, result, now)
    db.commit()
    return scan
