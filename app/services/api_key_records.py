from sqlalchemy.orm import Session
from app.models.api_key import ApiKey

def create_api_key_record(db: Session, organization_id: int, name: str, key_prefix: str, key_hash: str, created_by: str | None):
    record = ApiKey(
        organization_id=organization_id,
        name=name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        active=True,
        created_by=created_by,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def list_api_keys(db: Session, organization_id: int):
    return db.query(ApiKey).filter(ApiKey.organization_id == organization_id).order_by(ApiKey.created_at.desc()).all()

def get_api_key_by_hash(db: Session, key_hash: str):
    return db.query(ApiKey).filter(ApiKey.key_hash == key_hash, ApiKey.active == True).first()

def get_api_key_by_id(db: Session, organization_id: int, key_id: int):
    return db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.organization_id == organization_id).first()
