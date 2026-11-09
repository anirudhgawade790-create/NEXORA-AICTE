import os
import unittest
from datetime import datetime, timedelta

os.environ["APP_ENV"] = "development"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-only-secret-for-aph-tests-123456"

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.aph_rules import (
    APH_RULES,
    appeal_deadline,
    appeal_is_open,
    application_rule_metadata,
    workflow_path_for,
)
from app.database import Base
from app.models import (
    Application, ApplicationAppeal, ApplicationStage, AuditLogs, DeficiencyCompliance,
    Documents, EVCAppointments, Institution, ScrutinyObservations, User, WorkflowRules,
)
from app.routers.applications import create_application, file_appeal, record_external_decision
from app.routers.compliance import review_deficiency_compliance, submit_deficiency_compliance
from app.schemas.applications import AppealCreate, ApplicationCreate, DecisionRecordRequest
from app.schemas.compliance import DeficiencyComplianceReview, DeficiencyComplianceSubmit
from app.services.workflow_engine import next_rule, transition, unresolved_deficiencies


class AphWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        institution = Institution(name="Example Institute", region="South")
        self.session.add(institution)
        self.session.flush()
        self.institution = institution
        self.institution_user = User(
            email="institution@aph.test", full_name="Institution User",
            password_hash="unused", role="institution", institution_id=institution.id,
            is_active=True,
        )
        self.officer = User(
            email="officer@aph.test", full_name="Regional Officer",
            password_hash="unused", role="regional_officer", region="South",
            is_active=True,
        )
        self.bureau = User(
            email="bureau@aph.test", full_name="Bureau Officer",
            password_hash="unused", role="bureau_officer", is_active=True,
        )
        self.admin = User(
            email="admin@aph.test", full_name="Administrator",
            password_hash="unused", role="admin", is_active=True,
        )
        self.session.add_all([self.institution_user, self.officer, self.bureau, self.admin])
        self.session.flush()
        names = {
            "submission": "Application Submission",
            "self_disclosure": "Self-Disclosure",
            "processing": "Processing",
            "initial_scrutiny": "Scrutiny",
            "deficiency_check": "Re-Scrutiny",
            "evc_scheduling": "EVC Scheduling",
            "evc_completion": "EVC Completion",
            "committee_stage": "SAC / SHC",
            "authorised_decision": "Authorised Decision",
            "final_status": "Final Status",
        }
        for order, (key, name) in enumerate(names.items(), 1):
            self.session.add(WorkflowRules(
                stage_key=key,
                stage_name=name,
                stage_order=order,
                requires_scrutiny=key in {"initial_scrutiny", "deficiency_check"},
                requires_evc=key in {"evc_scheduling", "evc_completion"},
                requires_committee=key == "committee_stage",
                allowed_roles="institution,regional_officer,bureau_officer,evc_committee,admin",
                is_active=True,
            ))
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def make_application(self, rule_key, stage="submission", status="pending"):
        item = Application(
            id=f"APP-APH-{rule_key}",
            institution_id=self.institution.id,
            region="South",
            application_type=APH_RULES[rule_key]["label"],
            workflow_path=workflow_path_for(rule_key),
            aph_rule_key=rule_key,
            aph_rule_metadata=application_rule_metadata(rule_key),
            current_stage=stage,
            status=status,
            updated_at=datetime.utcnow() - timedelta(minutes=1),
        )
        self.session.add(item)
        self.session.flush()
        self.session.add(ApplicationStage(
            application_id=item.id,
            stage_key=stage,
            stage_name=stage,
            actor_user_id=self.institution_user.id,
            status="active",
        ))
        self.session.commit()
        return item

    def test_each_requested_category_has_a_source_backed_route_and_timeline(self):
        self.assertEqual(APH_RULES["eoa_self_disclosure"]["rule_category"], "category_1")
        self.assertEqual(APH_RULES["eoa_self_disclosure"]["processing_timeline"], "As per AICTE Public Notice")
        self.assertEqual(APH_RULES["change_site_location"]["rule_category"], "category_2")
        self.assertEqual(APH_RULES["change_site_location"]["processing_timeline"], "Year-round")
        self.assertIn("twice a year", APH_RULES["odl_online_learning"]["processing_timeline"])
        for key in (
            "increase_intake_additional_courses", "new_programme_level",
            "change_institution_name", "merger_of_institutions",
            "change_site_location", "closure_institution",
        ):
            self.assertIn("submission", APH_RULES[key]["stages"])
            self.assertIn("Annexure-2", APH_RULES[key]["required_documents"])
        for key in ("increase_intake_additional_courses", "new_programme_level", "merger_of_institutions", "change_site_location"):
            self.assertIn("initial_scrutiny", APH_RULES[key]["stages"])
            self.assertIn("evc_completion", APH_RULES[key]["stages"])
            self.assertIn("sac_shc_based_on_previous_processing_outcome", APH_RULES[key]["conditional_steps"])
        self.assertIn("initial_scrutiny", APH_RULES["change_institution_name"]["stages"])
        self.assertNotIn("evc_scheduling", APH_RULES["change_institution_name"]["stages"])
        self.assertIn("initial_scrutiny", APH_RULES["closure_institution"]["stages"])
        self.assertNotIn("evc_scheduling", APH_RULES["closure_institution"]["stages"])

    def test_eoa_self_disclosure_bypasses_scrutiny_and_evc(self):
        item = self.make_application("eoa_self_disclosure")
        rules = self.session.query(WorkflowRules).all()

        first = next_rule(rules, self.session.query(WorkflowRules).filter_by(
            stage_key="submission"
        ).one(), item.workflow_path, item, self.session)
        second = next_rule(rules, self.session.query(WorkflowRules).filter_by(
            stage_key="self_disclosure"
        ).one(), item.workflow_path, item, self.session)

        self.assertEqual(first.stage_key, "self_disclosure")
        self.assertEqual(second.stage_key, "processing")
        self.assertNotIn("initial_scrutiny", item.aph_rule_metadata["stages"])
        self.assertNotIn("evc_completion", item.aph_rule_metadata["stages"])

    def test_application_creation_persists_aph_rule_metadata_and_route(self):
        created = create_application(
            ApplicationCreate(
                application_type="Extension of Approval (Self-Disclosure)",
                aph_rule_key="eoa_self_disclosure",
            ),
            self.session,
            self.institution_user,
        )

        self.assertEqual(created["aph_rule_key"], "eoa_self_disclosure")
        self.assertEqual(created["workflow_stages"][1:3], ["self_disclosure", "processing"])
        self.assertEqual(created["processing_timeline"], "As per AICTE Public Notice")
        self.assertEqual(created["required_documents"], ["Annexure-2"])
        self.assertIn("Table 2.3", created["aph_rule_metadata"]["clauses"])
        self.assertIsNone(created["deadline"])

    def test_clause_2_6_core_course_minimum_is_validated_for_engineering(self):
        with self.assertRaises(HTTPException) as raised:
            create_application(
                ApplicationCreate(
                    application_type="Increase in Intake / Additional Courses",
                    aph_rule_key="increase_intake_additional_courses",
                    program_area="engineering_technology",
                    core_course_count=2,
                ),
                self.session,
                self.institution_user,
            )
        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("at least 3", raised.exception.detail)

    def test_intake_increase_requires_scrutiny_and_evc_and_skips_unneeded_rescrutiny(self):
        item = self.make_application("increase_intake_additional_courses")
        rules = self.session.query(WorkflowRules).all()
        submission = self.session.query(WorkflowRules).filter_by(stage_key="submission").one()
        scrutiny = self.session.query(WorkflowRules).filter_by(stage_key="initial_scrutiny").one()
        evc_completion = self.session.query(WorkflowRules).filter_by(stage_key="evc_completion").one()

        self.assertEqual(next_rule(rules, submission, item.workflow_path, item, self.session).stage_key, "initial_scrutiny")
        self.assertEqual(next_rule(rules, scrutiny, item.workflow_path, item, self.session).stage_key, "evc_scheduling")
        self.assertEqual(next_rule(rules, evc_completion, item.workflow_path, item, self.session).stage_key, "authorised_decision")

    def test_conditional_sac_shc_requires_explicit_audited_referral(self):
        item = self.make_application("increase_intake_additional_courses", "evc_completion")
        rules = self.session.query(WorkflowRules).all()
        evc = self.session.query(WorkflowRules).filter_by(stage_key="evc_completion").one()
        self.assertEqual(next_rule(rules, evc, item.workflow_path, item, self.session).stage_key, "authorised_decision")
        self.session.add(EVCAppointments(
            application_id=item.id,
            scheduled_date=datetime.utcnow(),
            location="Online",
            status="completed",
        ))
        self.session.commit()

        result = transition(self.session, item, "refer_committee", self.officer, "Prior processing outcome requires committee consideration.")

        self.assertTrue(result.committee_referral)
        self.assertEqual(result.current_stage, "committee_stage")
        self.assertEqual(self.session.query(AuditLogs).filter_by(action="application_refer_committee").count(), 1)

    def test_evc_must_be_completed_before_aph_route_can_advance(self):
        item = self.make_application("increase_intake_additional_courses", "evc_completion")

        with self.assertRaises(HTTPException) as raised:
            transition(self.session, item, "forward", self.officer, None)

        self.assertEqual(raised.exception.status_code, 409)

    def test_name_change_and_closure_have_scrutiny_without_standard_evc(self):
        for key in ("change_institution_name", "closure_institution"):
            item = self.make_application(key)
            rules = self.session.query(WorkflowRules).all()
            submission = self.session.query(WorkflowRules).filter_by(stage_key="submission").one()
            scrutiny = self.session.query(WorkflowRules).filter_by(stage_key="initial_scrutiny").one()
            self.assertEqual(next_rule(rules, submission, item.workflow_path, item, self.session).stage_key, "initial_scrutiny")
            self.assertEqual(next_rule(rules, scrutiny, item.workflow_path, item, self.session).stage_key, "authorised_decision")
            self.assertNotIn("evc_scheduling", APH_RULES[key]["stages"])
        self.assertEqual(APH_RULES["closure_institution"]["ter_charges"], "no_TER_charges")

    def test_aph_scrutiny_cannot_be_disabled_or_skipped(self):
        item = self.make_application("increase_intake_additional_courses")
        submission = self.session.query(WorkflowRules).filter_by(stage_key="submission").one()
        self.session.query(WorkflowRules).filter_by(stage_key="initial_scrutiny").update(
            {"requires_scrutiny": False}
        )
        self.session.commit()

        with self.assertRaises(HTTPException) as raised:
            next_rule(self.session.query(WorkflowRules).all(), submission, item.workflow_path, item, self.session)

        self.assertEqual(raised.exception.status_code, 409)

    def test_missing_annexure_two_blocks_starting_processing(self):
        item = self.make_application("change_institution_name")

        with self.assertRaises(HTTPException) as raised:
            transition(self.session, item, "forward", self.institution_user, None)

        self.assertEqual(raised.exception.status_code, 409)
        self.assertIn("Annexure-2", raised.exception.detail)
        self.assertEqual(item.current_stage, "submission")

    def test_uploading_annexure_two_does_not_decide_or_approve_application(self):
        item = self.make_application("eoa_self_disclosure")
        self.session.add(Documents(
            application_id=item.id,
            institution_id=self.institution.id,
            category="Annexure-2",
            file_name="annexure-2.pdf",
            stored_path="seeded://annexure-2",
            mime_type="application/pdf",
            file_size=10,
            uploaded_by=self.institution_user.id,
            status="under_verification",
        ))
        self.session.commit()

        result = transition(self.session, item, "forward", self.institution_user, None)

        self.assertEqual(result.current_stage, "self_disclosure")
        self.assertEqual(result.status, "pending")
        self.assertIsNone(result.decision_at)

    def test_unresolved_deficiencies_block_processing_and_decision_until_verified(self):
        item = self.make_application("increase_intake_additional_courses", "evc_completion")
        observation = ScrutinyObservations(
            application_id=item.id,
            officer_id=self.officer.id,
            observation_text="Faculty evidence is incomplete",
            is_deficiency=True,
            workflow_stage="evc_completion",
        )
        self.session.add(observation)
        self.session.flush()
        self.assertEqual(len(unresolved_deficiencies(self.session, item)), 1)
        evidence = Documents(
            application_id=item.id,
            institution_id=item.institution_id,
            category="Approval Supporting Documents",
            file_name="decision-order.pdf",
            stored_path="seeded://decision-order",
            mime_type="application/pdf",
            file_size=10,
            uploaded_by=self.institution_user.id,
            status="verified",
        )
        self.session.add(evidence)
        self.session.flush()
        item.current_stage = "final_status"
        with self.assertRaises(HTTPException) as raised:
            record_external_decision(
                item.id,
                DecisionRecordRequest(
                    outcome="approved", authority="executive_committee",
                    uploaded_at=datetime.utcnow(), evidence_document_id=evidence.id,
                    source_reference="decision-1",
                ),
                self.session,
                self.bureau,
            )
        self.assertEqual(raised.exception.status_code, 409)

    def test_external_decision_requires_uploaded_evidence_and_creates_audit_record(self):
        item = self.make_application("eoa_self_disclosure", "processing")
        payload = DecisionRecordRequest(
            outcome="approved",
            authority="council",
            uploaded_at=datetime.utcnow() - timedelta(hours=1),
            evidence_document_id=999,
            source_reference="APH order reference",
        )
        with self.assertRaises(HTTPException) as raised:
            record_external_decision(item.id, payload, self.session, self.bureau)
        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(item.status, "pending")

        evidence = Documents(
            application_id=item.id,
            institution_id=item.institution_id,
            category="Approval Supporting Documents",
            file_name="eoa-order.pdf",
            stored_path="seeded://eoa-order",
            mime_type="application/pdf",
            file_size=20,
            uploaded_by=self.institution_user.id,
            status="verified",
        )
        self.session.add(evidence)
        self.session.commit()
        payload.evidence_document_id = evidence.id

        result = record_external_decision(item.id, payload, self.session, self.bureau)

        self.assertEqual(result["status"], "approved")
        self.assertEqual(result["decision_document_id"], evidence.id)
        self.assertEqual(
            self.session.query(AuditLogs).filter_by(action="external_decision_recorded").count(),
            1,
        )

    def test_compliance_submissions_and_reviews_preserve_evidence_history(self):
        item = self.make_application("increase_intake_additional_courses", "evc_completion", "returned")
        observation = ScrutinyObservations(
            application_id=item.id,
            officer_id=self.officer.id,
            observation_text="Infrastructure evidence is incomplete",
            is_deficiency=True,
            workflow_stage="evc_completion",
        )
        self.session.add(observation)
        self.session.flush()
        document = Documents(
            application_id=item.id,
            institution_id=self.institution.id,
            category="Compliance Evidence",
            file_name="evidence.pdf",
            stored_path="seeded://evidence",
            mime_type="application/pdf",
            file_size=10,
            uploaded_by=self.institution_user.id,
            status="under_verification",
        )
        self.session.add(document)
        self.session.commit()

        first = submit_deficiency_compliance(
            item.id, observation.id,
            DeficiencyComplianceSubmit(evidence_document_id=document.id),
            self.session, self.institution_user,
        )
        review_deficiency_compliance(
            first["id"], DeficiencyComplianceReview(status="deficient", remarks="Submit the complete plan."),
            self.session, self.officer,
        )
        second = submit_deficiency_compliance(
            item.id, observation.id,
            DeficiencyComplianceSubmit(evidence_document_id=document.id),
            self.session, self.institution_user,
        )
        review_deficiency_compliance(
            second["id"], DeficiencyComplianceReview(status="verified", remarks="Observation addressed."),
            self.session, self.officer,
        )

        history = self.session.query(DeficiencyCompliance).filter_by(
            observation_id=observation.id
        ).order_by(DeficiencyCompliance.id).all()
        self.assertEqual([entry.status for entry in history], ["deficient", "verified"])
        self.assertTrue(all(entry.evidence_document_id == document.id for entry in history))
        self.assertEqual(
            self.session.query(AuditLogs).filter(
                AuditLogs.affected_record_type == "deficiency_compliance"
            ).count(),
            4,
        )
        self.assertEqual(unresolved_deficiencies(self.session, item), [])
        resubmitted = transition(self.session, item, "resubmit", self.institution_user, None)
        self.assertEqual(resubmitted.current_stage, "evc_completion")
        self.assertEqual(resubmitted.status, "pending")

    def test_appeal_deadline_is_exactly_seven_days_and_only_for_ec_decisions(self):
        uploaded = datetime(2026, 10, 1, 12, 0)
        self.assertEqual(appeal_deadline(uploaded, "executive_committee"), uploaded + timedelta(days=7))
        self.assertTrue(appeal_is_open(uploaded, "executive_committee", uploaded + timedelta(days=7)))
        self.assertFalse(appeal_is_open(
            uploaded, "executive_committee", uploaded + timedelta(days=7, seconds=1)
        ))
        self.assertIsNone(appeal_deadline(uploaded, "other"))

    def test_one_appeal_can_be_recorded_for_an_ec_decision_within_seven_days(self):
        item = self.make_application("change_institution_name", "final_status", "rejected")
        item.decision_at = datetime.utcnow() - timedelta(days=1)
        item.decision_authority = "executive_committee"
        item.decision_reference = "portal decision ref"
        self.session.commit()

        result = file_appeal(
            item.id, AppealCreate(reason="I am aggrieved by the uploaded decision."),
            self.session, self.institution_user,
        )

        self.assertEqual(result["clause"], "2.24")
        self.assertIn("does not file", result["note"])
        with self.assertRaises(HTTPException) as raised:
            file_appeal(
                item.id, AppealCreate(reason="Second attempt."),
                self.session, self.institution_user,
            )
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(self.session.query(ApplicationAppeal).filter_by(application_id=item.id).count(), 1)

    def test_appeal_after_seven_days_or_without_ec_decision_is_rejected(self):
        item = self.make_application("change_institution_name", "final_status", "rejected")
        item.decision_at = datetime.utcnow() - timedelta(days=8)
        item.decision_authority = "executive_committee"
        self.session.commit()
        with self.assertRaises(HTTPException) as raised:
            file_appeal(item.id, AppealCreate(reason="Late appeal."), self.session, self.institution_user)
        self.assertEqual(raised.exception.status_code, 409)
        item.decision_at = datetime.utcnow()
        item.decision_authority = "council"
        self.session.commit()
        with self.assertRaises(HTTPException) as raised:
            file_appeal(item.id, AppealCreate(reason="Not an EC decision."), self.session, self.institution_user)
        self.assertEqual(raised.exception.status_code, 409)

    def test_aph_final_stage_never_auto_approves_or_accepts_officer_rejection(self):
        item = self.make_application("change_institution_name", "final_status")
        with self.assertRaises(HTTPException) as raised:
            transition(self.session, item, "complete", self.bureau, None)
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(item.status, "pending")

    def test_unsupported_aph_workflow_action_is_rejected(self):
        item = self.make_application("change_institution_name", "initial_scrutiny")

        with self.assertRaises(HTTPException) as raised:
            transition(self.session, item, "skip_to_approval", self.officer, None)

        self.assertEqual(raised.exception.status_code, 400)
        with self.assertRaises(HTTPException) as raised:
            transition(self.session, item, "reject", self.officer, "Not approved.")
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(item.status, "pending")


if __name__ == "__main__":
    unittest.main()
