from pydantic import BaseModel, EmailStr

class AdminCreateUserRequest(BaseModel):
    username: str
    email: EmailStr | None = None
    password: str
    role: str = "analyst"

class InviteCreateRequest(BaseModel):
    email: EmailStr
    role: str = "analyst"

class OrgSettingsUpdateRequest(BaseModel):
    display_name: str | None = None
    logo_url: str | None = None
    primary_color: str | None = None
    report_footer: str | None = None
    timezone: str | None = None

class BillingCheckoutRequest(BaseModel):
    plan: str
