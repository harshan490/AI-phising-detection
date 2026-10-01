"""Combines the text-model probability with heuristic and threat-intel signals."""
from typing import Any, Dict, List

WEIGHTS = {"text": 0.45, "url": 0.25, "auth": 0.15, "attachment": 0.10, "sender": 0.05}
SUSPICIOUS_AT = 0.40
PHISHING_AT = 0.70
BLOCKLIST_FLOOR = 0.90


def verdict_for(risk: float) -> str:
    if risk >= PHISHING_AT:
        return "Phishing"
    if risk >= SUSPICIOUS_AT:
        return "Suspicious"
    return "Safe"


def compute_risk(text_prob: float, checks: List[Dict[str, Any]], blocklist_hit: bool,
                 top_terms: List[Dict[str, Any]]) -> Dict[str, Any]:
    components = {"text": round(text_prob, 4)}
    for cat in ("url", "auth", "attachment", "sender"):
        components[cat] = max((c["severity"] for c in checks if c["category"] == cat and c["triggered"]),
                              default=0.0)
    risk = sum(WEIGHTS[k] * v for k, v in components.items())
    overrides = []
    if blocklist_hit:
        risk = max(risk, BLOCKLIST_FLOOR)
        overrides.append("URL/domain on local blocklist: risk raised to at least 90")
    return {
        "risk_score": round(risk * 100, 1),
        "verdict": verdict_for(risk),
        "components": components,
        "weights": WEIGHTS,
        "overrides": overrides,
        "triggered_checks": [c for c in checks if c["triggered"]],
        "top_terms": top_terms,
    }
