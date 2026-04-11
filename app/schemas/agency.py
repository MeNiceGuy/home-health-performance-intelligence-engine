from pydantic import BaseModel
from typing import Any

class AgencyIntake(BaseModel):
    data: dict[str, Any]
    save_record: bool = True

class AgencyUpdateRequest(BaseModel):
    data: dict[str, Any]

class AgencyRecordOut(BaseModel):
    id: int
    organization_id: int
    agency_name: str
    state: str
    city: str | None = None
    ownership_type: str | None = None
    notes: str | None = None

    class Config:
        from_attributes = True
