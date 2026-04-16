from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.database import get_db
from app.models.models import User, Report
from app.schemas.schemas import UserCreate, UserLogin, ReportCreate
from app.core.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api")

@router.post("/register")
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "subscription_status": user.subscription_status}

@router.post("/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.email, "user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/reports")
def create_report(payload: ReportCreate, db: Session = Depends(get_db)):
    report = Report(agency_name=payload.agency_name, payload_json=payload.payload_json, result_json=payload.result_json)
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"id": report.id, "agency_name": report.agency_name}
