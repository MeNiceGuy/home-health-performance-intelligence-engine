from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ReportCreate(BaseModel):
    agency_name: str
    payload_json: str
    result_json: str | None = None
