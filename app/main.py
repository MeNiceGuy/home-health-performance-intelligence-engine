from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.organizations import router as organizations_router
from app.api.routes.agency_records import router as agency_records_router
from app.api.routes.reports import router as reports_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.risk import router as risk_router
from app.api.routes.audit import router as audit_router
from app.api.routes.admin import router as admin_router
from app.api.routes.invites import router as invites_router
from app.api.routes.billing import router as billing_router
from app.api.routes.api_keys import router as api_keys_router
from app.api.routes.password import router as password_router
from app.api.routes.usage import router as usage_router
from app.api.routes.client_api import router as client_api_router

app = FastAPI(title="Home Health Performance Intelligence Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(organizations_router)
app.include_router(agency_records_router)
app.include_router(reports_router)
app.include_router(dashboard_router)
app.include_router(risk_router)
app.include_router(audit_router)
app.include_router(admin_router)
app.include_router(invites_router)
app.include_router(billing_router)
app.include_router(api_keys_router)
app.include_router(password_router)
app.include_router(usage_router)
app.include_router(client_api_router)

@app.get("/health")
def health():
    return {"status": "ok"}
