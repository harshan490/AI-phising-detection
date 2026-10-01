from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.ai_model import load_metrics

router = APIRouter()


@router.get("/metrics")
def model_metrics(user: User = Depends(get_current_active_user)):
    metrics = load_metrics()
    if not metrics:
        raise HTTPException(status_code=404, detail="Metrics not available. Train the model first.")
    return metrics
