import os
import unittest

os.environ["APP_ENV"] = "development"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-only-secret-for-workflow-tests-123456"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    Application,
    ApplicationStage,
    AuditLogs,
    Institution,
    Notifications,
    User,
    WorkflowRules,
)
from app.services.workflow_engine import next_rule, transition
from app.workflow_paths import suggest_workflow_path
from fastapi import HTTPException


class WorkflowTransitionTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

        institution = Institution(name="Demo Institute", region="South")
        self.session.add(institution)
        self.session.flush()
        self.institution_user = User(
            email="institution@test.invalid",
            full_name="Institution User",
            password_hash="unused",
            role="institution",
            institution_id=institution.id,
            is_active=True,
        )
        self.officer = User(
            email="officer@test.invalid",
            full_name="Regional Officer",
            password_hash="unused",
            role="regional_officer",
            region="South",
            is_active=True,
        )
        self.session.add_all([self.institution_user, self.officer])
        self.session.flush()

        self.session.add_all([
            WorkflowRules(
                stage_key="initial_scrutiny",
                stage_name="Initial Scrutiny",
                stage_order=2,
                requires_scrutiny=True,
                allowed_roles="regional_officer,bureau_officer",
                deadline_days=15,
                is_active=True,
            ),
            WorkflowRules(
                stage_key="deficiency_check",
                stage_name="Deficiency Check",
                stage_order=3,
                requires_scrutiny=True,
                allowed_roles="regional_officer,bureau_officer",
                deadline_days=10,
                is_active=True,
            ),
        ])
        self.application = Application(
            id="APP-2026-TEST",
            institution_id=institution.id,
            region="South",
            application_type="New Institution",
            current_stage="initial_scrutiny",
            status="pending",
            assigned_officer_id=self.officer.id,
            priority="Medium",
        )
        self.session.add(self.application)
        self.session.flush()
        self.active_stage = ApplicationStage(
            application_id=self.application.id,
            stage_key="initial_scrutiny",
            stage_name="Initial Scrutiny",
            actor_user_id=self.institution_user.id,
            status="active",
        )
        self.session.add(self.active_stage)
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_forward_advances_stage_and_records_audit_and_notification(self):
        result = transition(self.session, self.application, "forward", self.officer, None)

        self.assertEqual(result.current_stage, "deficiency_check")
        self.assertEqual(result.status, "pending")
        self.assertEqual(self.active_stage.status, "completed")
        self.assertEqual(
            self.session.query(AuditLogs).filter_by(action="application_forward").count(),
            1,
        )
        self.assertGreater(self.session.query(Notifications).count(), 0)

    def test_application_path_skips_stages_not_in_selected_route(self):
        rules = [
            WorkflowRules(
                stage_key=stage_key,
                stage_name=stage_key,
                stage_order=order,
                requires_scrutiny=stage_key in {"initial_scrutiny", "deficiency_check"},
                requires_evc=stage_key in {"evc_scheduling", "evc_completion"},
                requires_committee=stage_key == "committee_stage",
                allowed_roles="regional_officer",
                is_active=True,
            )
            for order, stage_key in enumerate(
                [
                    "submission", "initial_scrutiny", "deficiency_check",
                    "evc_scheduling", "evc_completion", "committee_stage",
                    "authorised_decision", "final_status",
                ],
                start=1,
            )
        ]
        initial = next(rule for rule in rules if rule.stage_key == "initial_scrutiny")
        deficiency = next(rule for rule in rules if rule.stage_key == "deficiency_check")
        evc_completion = next(rule for rule in rules if rule.stage_key == "evc_completion")

        scrutiny_only = next_rule(rules, initial, "scrutiny_only")
        scrutiny_with_evc = next_rule(rules, initial, "scrutiny_evc")
        full_review = next_rule(rules, initial, "scrutiny_evc_sac_shc")

        self.assertEqual(scrutiny_only.stage_key, "deficiency_check")
        self.assertEqual(scrutiny_with_evc.stage_key, "deficiency_check")
        self.assertEqual(full_review.stage_key, "deficiency_check")
        self.assertEqual(next_rule(rules, deficiency, "scrutiny_only").stage_key, "authorised_decision")
        self.assertEqual(next_rule(rules, deficiency, "scrutiny_evc").stage_key, "evc_scheduling")
        self.assertEqual(next_rule(rules, evc_completion, "scrutiny_evc").stage_key, "authorised_decision")
        self.assertEqual(
            next_rule(rules, evc_completion, "scrutiny_evc_sac_shc").stage_key,
            "committee_stage",
        )

    def test_evc_only_route_starts_at_evc_after_submission(self):
        rules = [
            WorkflowRules(
                stage_key=stage_key,
                stage_name=stage_key,
                stage_order=order,
                requires_evc=stage_key in {"evc_scheduling", "evc_completion"},
                allowed_roles="regional_officer",
                is_active=True,
            )
            for order, stage_key in enumerate(
                ["submission", "initial_scrutiny", "evc_scheduling", "evc_completion"],
                start=1,
            )
        ]

        result = next_rule(rules, rules[0], "only_evc")

        self.assertEqual(result.stage_key, "evc_scheduling")

    def test_application_type_suggests_an_editable_demo_route(self):
        self.assertEqual(suggest_workflow_path("New Institution")[0], "scrutiny_evc_sac_shc")
        self.assertEqual(suggest_workflow_path("Renewal application")[0], "scrutiny_only")
        self.assertEqual(suggest_workflow_path("Program Expansion")[0], "scrutiny_evc")
        self.assertEqual(suggest_workflow_path("EVC visit")[0], "only_evc")
        self.assertEqual(suggest_workflow_path("Other category")[0], "scrutiny_evc_sac_shc")

    def test_return_requires_a_reason(self):
        with self.assertRaises(HTTPException) as raised:
            transition(self.session, self.application, "return", self.officer, "  ")

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(self.application.status, "pending")

    def test_only_allowed_roles_can_advance_a_stage(self):
        with self.assertRaises(HTTPException) as raised:
            transition(self.session, self.application, "forward", self.institution_user, None)

        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(self.application.current_stage, "initial_scrutiny")

    def test_owning_institution_can_resubmit_returned_application(self):
        transition(self.session, self.application, "return", self.officer, "Please correct evidence")

        result = transition(
            self.session, self.application, "resubmit", self.institution_user, None
        )

        self.assertEqual(result.status, "pending")
        self.assertEqual(result.current_stage, "initial_scrutiny")
        self.assertEqual(
            self.session.query(ApplicationStage)
            .filter_by(application_id=self.application.id, status="active")
            .count(),
            1,
        )

    def test_institution_cannot_access_another_institutions_application(self):
        other_institution = Institution(name="Other Institute", region="South")
        self.session.add(other_institution)
        self.session.flush()
        other_user = User(
            email="other@test.invalid",
            full_name="Other Institution User",
            password_hash="unused",
            role="institution",
            institution_id=other_institution.id,
            is_active=True,
        )
        self.session.add(other_user)
        self.session.commit()

        with self.assertRaises(HTTPException) as raised:
            transition(self.session, self.application, "resubmit", other_user, None)

        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(self.application.status, "pending")

    def test_final_application_cannot_be_reopened(self):
        self.session.query(Application).filter_by(id=self.application.id).update(
            {"status": "approved"}
        )
        self.session.commit()
        self.session.refresh(self.application)

        with self.assertRaises(HTTPException) as raised:
            transition(self.session, self.application, "forward", self.officer, None)

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(self.application.status, "approved")


if __name__ == "__main__":
    unittest.main()
