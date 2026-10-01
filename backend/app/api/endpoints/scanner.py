import json
import logging
from collections import Counter

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.config import settings
from app.models.scan import IOC, Scan
from app.models.user import User
from app.schemas.email import ScanJobInitResponse, ScanJobStatus, URLScanRequest
from app.services.scan_pipeline import scan_and_store
from app.services.threat_intel import threat_intel

logger = logging.getLogger(__name__)
router = APIRouter()


def _scans_for(user: User, db: Session):
    q = db.query(Scan)
    return q if user.role == "admin" else q.filter(Scan.user_id == user.id)


@router.post("/upload-email", response_model=ScanJobInitResponse)
async def upload_and_scan_email(file: UploadFile = File(...), db: Session = Depends(get_db),
                                user: User = Depends(get_current_active_user)):
    if not (file.filename or "").lower().endswith(".eml"):
        raise HTTPException(status_code=400, detail="Only .eml files are supported")
    raw = await file.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(raw) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
    if not raw.strip():
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        scan = scan_and_store(raw, file.filename, user.id, db)
    except Exception:
        logger.exception("Scan failed for %s", file.filename)
        raise HTTPException(status_code=500, detail="Scan failed")
    return {"scan_id": scan.id, "message": "Email scanned"}


@router.get("/status/{scan_id}", response_model=ScanJobStatus)
def get_scan_status(scan_id: str, db: Session = Depends(get_db),
                    user: User = Depends(get_current_active_user)):
    scan = _scans_for(user, db).filter(Scan.id == scan_id).first()
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan ID not found")
    result = json.loads(scan.result_json)
    return {"scan_id": scan.id, "status": "completed", "current_step": "done",
            "logs": result.get("logs", []), "result": result}


@router.post("/scan-url")
def scan_url(request: URLScanRequest, user: User = Depends(get_current_active_user)):
    return threat_intel.check_url(request.url)


@router.get("/dashboard-stats")
def get_dashboard_stats(db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    scans = _scans_for(user, db).order_by(Scan.created_at.desc()).all()
    counts = Counter(s.verdict for s in scans)
    total = len(scans)
    phishing, suspicious = counts.get("Phishing", 0), counts.get("Suspicious", 0)

    threat_level = "No data"
    if total:
        ratio = (phishing + 0.5 * suspicious) / total
        threat_level = "Critical" if ratio > 0.5 else "Elevated" if ratio > 0.2 else "Normal"

    per_day = Counter(s.created_at.strftime("%Y-%m-%d") for s in scans if s.created_at)
    check_counts = Counter()
    for s in scans:
        for c in json.loads(s.result_json).get("triggered_checks", []):
            check_counts[c["name"]] += 1

    return {
        "stats": {"totalScans": total, "phishingCaught": phishing, "suspicious": suspicious,
                  "safeEmails": counts.get("Safe", 0), "threatLevel": threat_level},
        "verdictCounts": {k: counts.get(k, 0) for k in ("Safe", "Suspicious", "Phishing")},
        "scansPerDay": [{"date": d, "count": n} for d, n in sorted(per_day.items())],
        "topChecks": [{"name": n, "count": c} for n, c in check_counts.most_common(8)],
        "recentScans": [{"id": s.id, "subject": s.subject or "No Subject", "sender": s.sender,
                         "status": s.verdict, "risk": s.risk_score,
                         "date": s.created_at.strftime("%d %b %I:%M %p") if s.created_at else ""}
                        for s in scans[:10]],
    }


@router.get("/iocs")
def list_iocs(limit: int = 200, db: Session = Depends(get_db),
              user: User = Depends(get_current_active_user)):
    rows = db.query(IOC).order_by(IOC.hit_count.desc(), IOC.last_seen.desc()).limit(min(limit, 1000)).all()
    return [{"type": r.type, "value": r.value, "hits": r.hit_count, "verdict": r.max_verdict,
             "first_seen": r.first_seen.isoformat() if r.first_seen else None,
             "last_seen": r.last_seen.isoformat() if r.last_seen else None} for r in rows]
