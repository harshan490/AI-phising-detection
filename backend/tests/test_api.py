import pytest
from fastapi.testclient import TestClient

from app.main import app
from conftest import DISCORD_EML, LOOKALIKE_EML, SCAM_EML

client = TestClient(app)


def _token(email):
    client.post("/api/v1/auth/register", json={"email": email, "password": "Str0ngPassw0rd!"})
    r = client.post("/api/v1/auth/login", data={"username": email, "password": "Str0ngPassw0rd!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def auth():
    return _token("analyst1@example.com")


def scan(path, headers):
    r = client.post("/api/v1/scanner/upload-email", headers=headers,
                    files={"file": (path.name, path.read_bytes(), "message/rfc822")})
    assert r.status_code == 200, r.text
    s = client.get(f"/api/v1/scanner/status/{r.json()['scan_id']}", headers=headers)
    assert s.status_code == 200
    return s.json()["result"]


def test_requires_auth():
    assert client.get("/api/v1/scanner/dashboard-stats").status_code == 401
    assert client.get("/api/v1/model/metrics").status_code == 401


def test_rejects_non_eml(auth):
    r = client.post("/api/v1/scanner/upload-email", headers=auth, files={"file": ("a.txt", b"x")})
    assert r.status_code == 400


def test_rejects_large_file(auth):
    r = client.post("/api/v1/scanner/upload-email", headers=auth,
                    files={"file": ("big.eml", b"a" * (10 * 1024 * 1024 + 1))})
    assert r.status_code == 413


def test_scam_sample_flagged(auth):
    res = scan(SCAM_EML, auth)
    assert res["verdict"] in ("Phishing", "Suspicious"), (res["risk_score"], res["components"])


def test_discord_sample_safe(auth):
    res = scan(DISCORD_EML, auth)
    assert res["verdict"] == "Safe", (res["risk_score"], res["components"], res["triggered_checks"])


def test_lookalike_fixture_phishing(auth):
    res = scan(LOOKALIKE_EML, auth)
    assert res["verdict"] == "Phishing", (res["risk_score"], res["components"])
    ids = {c["id"] for c in res["triggered_checks"]}
    assert {"lookalike_sender_domain", "link_text_mismatch", "risky_attachment"} <= ids


def test_users_cannot_read_each_others_scans(auth):
    r = client.post("/api/v1/scanner/upload-email", headers=auth,
                    files={"file": ("x.eml", LOOKALIKE_EML.read_bytes())})
    other = _token("analyst2@example.com")
    assert client.get(f"/api/v1/scanner/status/{r.json()['scan_id']}", headers=other).status_code == 404
    assert client.get("/api/v1/scanner/dashboard-stats", headers=other).json()["stats"]["totalScans"] == 0


def test_dashboard_and_iocs(auth):
    stats = client.get("/api/v1/scanner/dashboard-stats", headers=auth).json()
    assert stats["stats"]["totalScans"] >= 3
    iocs = client.get("/api/v1/scanner/iocs", headers=auth).json()
    assert any(i["value"] == "paypa1.com" and i["type"] == "domain" for i in iocs)


def test_model_metrics(auth):
    m = client.get("/api/v1/model/metrics", headers=auth).json()
    assert {"accuracy", "precision", "recall", "f1", "roc_auc"} <= set(m)
