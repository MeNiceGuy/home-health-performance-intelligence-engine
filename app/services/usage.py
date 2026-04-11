from sqlalchemy.orm import Session
from app.models.usage_event import UsageEvent

def append_usage_event(
    db: Session,
    event_type: str,
    units: int = 1,
    organization_id: int | None = None,
    username: str | None = None,
    api_key_prefix: str | None = None,
    detail: str | None = None,
):
    event = UsageEvent(
        organization_id=organization_id,
        username=username,
        api_key_prefix=api_key_prefix,
        event_type=event_type,
        units=units,
        detail=detail,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def summarize_usage(db: Session, organization_id: int):
    events = db.query(UsageEvent).filter(UsageEvent.organization_id == organization_id).all()
    summary = {}
    total_units = 0
    for e in events:
        summary[e.event_type] = summary.get(e.event_type, 0) + e.units
        total_units += e.units
    return {"total_units": total_units, "by_event_type": summary}
