from app.db.session import Base, engine
from app.models.user import User
from app.models.organization import Organization
from app.models.agency_record import AgencyRecord
from app.models.report_record import ReportRecord
from app.models.audit_event import AuditEvent
from app.models.invite import Invite
from app.models.org_settings import OrgSettings
from app.models.subscription import Subscription
from app.models.password_reset import PasswordResetToken
from app.models.api_key import ApiKey
from app.models.usage_event import UsageEvent

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
