from fastapi import APIRouter, HTMLResponse
from pathlib import Path
from app.services.risk_engine import calculate_risk_level, confidence_level
from app.services.ollama_service import generate_home_health_report

router = APIRouter()

@router.get("/")
def home():
    return {"app":"Home Health Intelligence SaaS"}

@router.post("/score")
def score(payload: dict):
    risk = calculate_risk_level(payload)
    confidence = confidence_level(payload)

    report_text = generate_home_health_report(payload)

    Path("reports").mkdir(exist_ok=True)
    Path("reports/full_report.txt").write_text(report_text, encoding="utf-8")

    return {
        "risk": risk,
        "confidence": confidence,
        "report_file": "/reports/full_report.txt"
    }
