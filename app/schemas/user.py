from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr | None = None
    password: str
    role: str = "analyst"

class UserOut(BaseModel):
    id: int
    username: str
    email: str | None = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True
