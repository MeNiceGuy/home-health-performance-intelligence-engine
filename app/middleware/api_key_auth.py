from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.api_keys import hash_api_key
from app.services.api_key_records import get_api_key_by_hash

def get_api_client(x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
    record = get_api_key_by_hash(db, hash_api_key(x_api_key))
    if not record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return record
