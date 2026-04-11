from pydantic import BaseModel, EmailStr

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str

class ApiKeyCreateRequest(BaseModel):
    name: str

class ApiKeyToggleRequest(BaseModel):
    active: bool
