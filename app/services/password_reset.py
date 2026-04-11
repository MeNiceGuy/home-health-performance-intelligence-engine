from datetime import datetime, timedelta, timezone
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app.core.config import RESET_TOKEN_SECRET, APP_BASE_URL
from app.models.user import User
from app.models.password_reset import PasswordResetToken

serializer = URLSafeTimedSerializer(RESET_TOKEN_SECRET)

def create_reset_token(db: Session, user: User):
    token = serializer.dumps({"user_id": user.id, "email": user.email})
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    record = PasswordResetToken(user_id=user.id, token=token, used=False, expires_at=expires_at)
    db.add(record)
    db.commit()
    db.refresh(record)
    return {
        "token": token,
        "reset_url": f"{APP_BASE_URL}/reset-password?token={token}",
        "expires_at": expires_at,
    }

def get_reset_record(db: Session, token: str):
    return db.query(PasswordResetToken).filter(PasswordResetToken.token == token).first()
