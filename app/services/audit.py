from sqlalchemy.orm import Session
from app.models.audit_event import AuditEvent

def append_audit_event(
    db: Session,
    action: str,
    detail: str = "",
    organization_id: int | None = None,
    username: str | None = None,
    agency_name: str | None = None,
    ip_address: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        organization_id=organization_id,
        username=username,
        action=action,
        detail=detail,
        agency_name=agency_name,
        ip_address=ip_address,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def list_audit_events(db: Session, organization_id: int | None, limit: int = 50) -> list[AuditEvent]:
    query = db.query(AuditEvent)
    if organization_id is not None:
        query = query.filter(AuditEvent.organization_id == organization_id)
    return query.order_by(AuditEvent.created_at.desc()).limit(limit).all()
