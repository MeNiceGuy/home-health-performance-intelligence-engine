from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.api_key_auth import get_api_client
from app.services.usage import append_usage_event

router = APIRouter(prefix="/client-api", tags=["client-api"])

@router.get("/health")
def client_api_health(api_client = Depends(get_api_client), db: Session = Depends(get_db)):
    append_usage_event(
        db=db,
        organization_id=api_client.organization_id,
        api_key_prefix=api_client.key_prefix,
        event_type="client_api_health",
        units=1,
        detail="External API health check",
    )
    return {"status": "ok", "organization_id": api_client.organization_id}
