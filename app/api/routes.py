from fastapi import APIRouter
from app.services.risk_engine import calculate_risk_level, confidence_level
router = APIRouter()

@router.get("/health")
def health():
    return {"status":"ok"}

@router.post("/score")
def score(payload: dict):
    return {
        "risk": calculate_risk_level(payload),
        "confidence": confidence_level(payload)
    }
