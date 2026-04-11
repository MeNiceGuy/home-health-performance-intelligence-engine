from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.get("/me")
def my_organization(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.organization_id is None:
        return {"organization": None}
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    return {"organization": {"id": org.id, "name": org.name, "slug": org.slug} if org else None}
