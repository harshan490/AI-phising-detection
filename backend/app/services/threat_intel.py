"""Threat intelligence: local offline blocklist + optional external lookups.

External lookups (VirusTotal, URLhaus) run only when their API key env var is set,
with a short timeout and a DB cache. Nothing is ever fabricated: when a source is
not queried, the result says so.
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.scan import TICache
from app.services.heuristics import host_of, registrable

logger = logging.getLogger(__name__)
BLOCKLIST_PATH = Path(__file__).resolve().parents[2] / "data" / "blocklist.txt"
LOCAL_LABEL = "Local threat intel (offline)"


def load_blocklist(path: Path = BLOCKLIST_PATH) -> set:
    if not path.exists():
        return set()
    return {l.strip().lower() for l in path.read_text().splitlines()
            if l.strip() and not l.lstrip().startswith("#")}


class ThreatIntelService:
    def __init__(self):
        self.blocklist = load_blocklist()

    def blocklisted(self, host: str) -> bool:
        host = host.lower()
        return host in self.blocklist or registrable(host) in self.blocklist

    def check_url(self, url: str) -> Dict[str, Any]:
        host = host_of(url)
        hit = bool(host) and self.blocklisted(host)
        return {"url": url, "domain": host, "malicious": hit, "source": LOCAL_LABEL,
                "evidence": "on local blocklist" if hit else "not on local blocklist"}

    # ----------------------------------------------------------- external
    @property
    def external_sources(self) -> List[str]:
        out = []
        if settings.VT_API_KEY:
            out.append("virustotal")
        if settings.URLHAUS_AUTH_KEY:
            out.append("urlhaus")
        return out

    def _cached(self, db: Session, source: str, key: str):
        row = db.query(TICache).filter_by(source=source, key=key).first()
        if row:
            fetched = row.fetched_at if row.fetched_at.tzinfo else row.fetched_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - fetched < timedelta(hours=settings.TI_CACHE_HOURS):
                return json.loads(row.result_json)
        return None

    def _store(self, db: Session, source: str, key: str, result: Dict[str, Any]):
        row = db.query(TICache).filter_by(source=source, key=key).first() or TICache(source=source, key=key)
        row.result_json = json.dumps(result)
        row.fetched_at = datetime.now(timezone.utc)
        db.add(row)
        db.commit()

    def _virustotal(self, domain: str) -> Dict[str, Any]:
        r = requests.get(f"https://www.virustotal.com/api/v3/domains/{domain}",
                         headers={"x-apikey": settings.VT_API_KEY}, timeout=settings.TI_TIMEOUT_SECONDS)
        if r.status_code == 404:
            return {"malicious": False, "detail": "unknown to VirusTotal"}
        r.raise_for_status()
        stats = r.json()["data"]["attributes"].get("last_analysis_stats", {})
        return {"malicious": stats.get("malicious", 0) > 0,
                "detail": f"{stats.get('malicious', 0)} malicious / {sum(stats.values())} engines"}

    def _urlhaus(self, domain: str) -> Dict[str, Any]:
        r = requests.post("https://urlhaus-api.abuse.ch/v1/host/", data={"host": domain},
                          headers={"Auth-Key": settings.URLHAUS_AUTH_KEY}, timeout=settings.TI_TIMEOUT_SECONDS)
        r.raise_for_status()
        data = r.json()
        listed = data.get("query_status") == "ok"
        return {"malicious": listed,
                "detail": f"{data.get('url_count', 0)} URLs listed" if listed else data.get("query_status")}

    def external_lookup(self, db: Session, domains: Iterable[str]) -> Dict[str, Any]:
        sources = self.external_sources
        if not sources:
            return {"status": "external TI not configured", "results": []}
        results = []
        for domain in list(dict.fromkeys(domains))[: settings.TI_MAX_LOOKUPS_PER_SCAN]:
            for src in sources:
                res = self._cached(db, src, domain)
                if res is None:
                    try:
                        res = (self._virustotal if src == "virustotal" else self._urlhaus)(domain)
                        self._store(db, src, domain, res)
                    except Exception:
                        logger.exception("%s lookup failed for %s", src, domain)
                        res = {"malicious": None, "detail": "lookup failed / timed out"}
                results.append({"source": src, "domain": domain, **res})
        return {"status": "queried: " + ", ".join(sources), "results": results}


threat_intel = ThreatIntelService()
