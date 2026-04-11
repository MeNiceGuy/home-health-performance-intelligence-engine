from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.user import User
from app.services.usage import summarize_usage

router = APIRouter(prefix="/usage", tags=["usage"])

@router.get("")
def usage_summary(
    current_user: User = Depends(require_role("admin", "analyst")),
    db: Session = Depends(get_db),
):
    if current_user.organization_id is None:
        return {"total_units": 0, "by_event_type": {}}
    return summarize_usage(db, current_user.organization_id)
