import os
import unittest
from datetime import datetime, timedelta

os.environ["APP_ENV"] = "development"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-only-secret-for-escalation-tests-123456"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base
from app.models import (
    Application,
    AuditLogs,
    ComplianceSubmissions,
    Documents,
    EVCAppointments,
    Escalations,
    Institution,
    Notifications,
    Undertakings,
    User,
)
from app.services.scheduler import run_monitor


class OverdueEscalationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.smtp_values = (settings.SMTP_HOST, settings.SMTP_FROM, settings.SMTP_USER)
        settings.SMTP_HOST = ""
        settings.SMTP_FROM = ""
        settings.SMTP_USER = ""

        institution = Institution(name="Example Institute", region="South")
        self.session.add(institution)
        self.session.flush()
        self.institution_id = institution.id
        self.institution_user = User(
            email="institution@test.invalid",
            full_name="Institution User",
            password_hash="unused",
            role="institution",
            institution_id=institution.id,
            is_active=True,
        )
        self.regional_officer = User(
            email="regional@test.invalid",
            full_name="Regional Officer",
            password_hash="unused",
            role="regional_officer",
            region="South",
            is_active=True,
        )
        self.bureau_officer = User(
            email="bureau@test.invalid",
            full_name="Bureau Officer",
            password_hash="unused",
            role="bureau_officer",
            is_active=True,
        )
        self.evc_user = User(
            email="evc@test.invalid",
            full_name="EVC Committee",
            password_hash="unused",
            role="evc_committee",
            is_active=True,
        )
        self.admin = User(
            email="admin@test.invalid",
            full_name="Administrator",
            password_hash="unused",
            role="admin",
            is_active=True,
        )
        self.session.add_all([
            self.institution_user,
            self.regional_officer,
            self.bureau_officer,
            self.evc_user,
            self.admin,
        ])
        self.session.flush()

        application = Application(
            id="APP-TEST-OVERDUE",
            institution_id=institution.id,
            region="South",
            application_type="Renewal",
            current_stage="final_status",
            status="pending",
        )
        self.session.add(application)
        self.session.flush()
        overdue_date = datetime.utcnow() - timedelta(days=8)
        self.session.add_all([
            ComplianceSubmissions(
                institution_id=institution.id,
                application_id=application.id,
                description="Submit undertaking evidence",
                due_date=overdue_date,
            ),
            Undertakings(
                institution_id=institution.id,
                application_id=application.id,
                description="Renew institutional undertaking",
                due_date=overdue_date,
            ),
            Documents(
                application_id=application.id,
                institution_id=institution.id,
                category="Lease Documents",
                file_name="lease.pdf",
                stored_path="demo/lease.pdf",
                mime_type="application/pdf",
                file_size=100,
                uploaded_by=self.institution_user.id,
                expiry_date=overdue_date,
                status="verified",
            ),
        ])
        self.session.commit()

    def tearDown(self):
        settings.SMTP_HOST, settings.SMTP_FROM, settings.SMTP_USER = self.smtp_values
        self.session.close()
        self.engine.dispose()

    def test_compliance_and_expired_documents_escalate_idempotently(self):
        result = run_monitor(self.session)

        self.assertEqual(result["overdue_compliance"], 2)
        self.assertEqual(result["new_compliance_escalations"], 4)
        self.assertEqual(result["new_document_escalations"], 2)
        self.assertEqual(self.session.query(Escalations).count(), 6)
        self.assertEqual(
            self.session.query(Escalations).filter_by(to_user_id=self.regional_officer.id).count(),
            3,
        )
        self.assertEqual(
            self.session.query(Escalations).filter_by(to_user_id=self.bureau_officer.id).count(),
            3,
        )
        self.assertEqual(
            self.session.query(AuditLogs).filter_by(action="escalation_created").count(),
            6,
        )
        self.assertGreater(
            self.session.query(Notifications).filter_by(event_type="escalation").count(),
            0,
        )

        second_result = run_monitor(self.session)

        self.assertEqual(second_result["new_compliance_escalations"], 0)
        self.assertEqual(second_result["new_document_escalations"], 0)
        self.assertEqual(self.session.query(Escalations).count(), 6)

    def test_overdue_evc_stages_and_missed_visits_get_separate_escalations(self):
        application = self.session.query(Application).one()
        application.current_stage = "evc_scheduling"
        application.deadline = datetime.utcnow() - timedelta(days=8)
        appointment = EVCAppointments(
            application_id=application.id,
            scheduled_date=datetime.utcnow() - timedelta(days=8),
            location="Demo venue",
            status="scheduled",
        )
        self.session.add(appointment)
        self.session.commit()

        result = run_monitor(self.session)

        self.assertEqual(result["overdue_evc_escalations"], 2)
        self.assertEqual(result["overdue_evc_visits"], 2)
        self.assertEqual(
            self.session.query(Escalations).filter_by(record_type="evc").count(),
            4,
        )
        self.assertEqual(
            self.session.query(Notifications).filter_by(event_type="evc_overdue").count(),
            2,
        )
        self.assertEqual(
            self.session.query(Notifications).filter_by(event_type="evc_visit_overdue").count(),
            2,
        )

        repeated = run_monitor(self.session)

        self.assertEqual(repeated["overdue_evc_escalations"], 0)
        self.assertEqual(repeated["overdue_evc_visits"], 0)
        self.assertEqual(
            self.session.query(Escalations).filter_by(record_type="evc").count(),
            4,
        )

    def test_upcoming_evc_stage_and_visit_get_reminders_once(self):
        application = self.session.query(Application).one()
        application.current_stage = "evc_scheduling"
        application.deadline = datetime.utcnow() + timedelta(days=2)
        appointment = EVCAppointments(
            application_id=application.id,
            scheduled_date=datetime.utcnow() + timedelta(days=2),
            location="Demo venue",
            status="scheduled",
        )
        self.session.add(appointment)
        self.session.commit()

        result = run_monitor(self.session)

        self.assertEqual(result["upcoming_evc_reminders"], 4)
        self.assertEqual(
            self.session.query(Notifications).filter_by(event_type="evc_due_soon").count(),
            2,
        )
        self.assertEqual(
            self.session.query(Notifications).filter_by(event_type="evc_visit_due_soon").count(),
            2,
        )

        repeated = run_monitor(self.session)
        self.assertEqual(repeated["upcoming_evc_reminders"], 0)


if __name__ == "__main__":
    unittest.main()
