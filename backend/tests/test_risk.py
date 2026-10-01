from app.services.risk import compute_risk, verdict_for


def test_thresholds():
    assert verdict_for(0.39) == "Safe"
    assert verdict_for(0.40) == "Suspicious"
    assert verdict_for(0.70) == "Phishing"


def test_formula_and_override():
    checks = [{"category": "url", "severity": 1.0, "triggered": True},
              {"category": "auth", "severity": 0.4, "triggered": True},
              {"category": "sender", "severity": 0.9, "triggered": False}]
    r = compute_risk(0.5, checks, False, [])
    assert r["risk_score"] == round((0.45 * 0.5 + 0.25 * 1.0 + 0.15 * 0.4) * 100, 1)
    assert compute_risk(0.0, [], True, [])["risk_score"] == 90.0
