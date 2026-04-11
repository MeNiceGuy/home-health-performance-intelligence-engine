from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr | None = None
    password: str
    role: str = "analyst"
    organization_name: str
    organization_slug: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str | None = None
    role: str
    is_active: bool
    organization_id: int | None = None

    class Config:
        from_attributes = True
