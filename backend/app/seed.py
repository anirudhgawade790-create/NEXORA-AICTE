"""Idempotent reference and synthetic demo seed data for the NEXORA prototype.

The shared demo password is documented in the README.
"""

from sqlalchemy.orm import Session

from app import models
from app.security import hash_password
from datetime import datetime, timedelta

# Five reference regions used across the prototype.
REGIONS = ["North", "South", "East", "West", "Central"]

# Reference document categories (a DocumentCategory table is added in a later
# phase; for now these are the canonical category strings).
DOCUMENT_CATEGORIES = [
    "Lease Documents",
    "Land and Building Documents",
    "Institutional Undertakings",
    "Approval Supporting Documents",
    "Compliance Evidence",
    "Other Prescribed Documents",
]

# Shared dev password for all demo users (documented in the README).
DEMO_PASSWORD = "demo1234"


def seed_demo_data(db: Session) -> None:
    # Configurable workflow pipeline rules (8 stages, in order).
    workflow_rules = [
        # (stage_key, stage_name, order, requires_scrutiny, requires_evc,
        #  requires_committee, allowed_roles, deadline_days)
        ("submission", "Application Submission", 1, False, False, False,
         "institution", 0),
        ("initial_scrutiny", "Initial Scrutiny", 2, True, False, False,
         "regional_officer,bureau_officer", 15),
        ("deficiency_check", "Deficiency Check", 3, True, False, False,
         "regional_officer,bureau_officer", 10),
        ("evc_scheduling", "EVC Scheduling", 4, False, True, False,
         "regional_officer,bureau_officer,evc_committee", 20),
        ("evc_completion", "EVC Completion", 5, False, True, False,
         "evc_committee,regional_officer", 30),
        ("committee_stage", "SAC / SHC / Committee Stage", 6, False, False, True,
         "bureau_officer,admin", 30),
        ("authorised_decision", "Authorised Decision", 7, False, False, False,
         "bureau_officer,admin", 15),
        ("final_status", "Final Application Status", 8, False, False, False,
         "bureau_officer,admin", None),
    ]
    for stage_key, stage_name, order, req_s, req_e, req_c, roles, days in workflow_rules:
        existing_rule = db.query(models.WorkflowRules).filter_by(stage_key=stage_key).first()
        if existing_rule:
            continue
        db.add(models.WorkflowRules(
            stage_key=stage_key,
            stage_name=stage_name,
            stage_order=order,
            requires_scrutiny=req_s,
            requires_evc=req_e,
            requires_committee=req_c,
            allowed_roles=roles,
            deadline_days=days,
            is_active=True,
        ))

    # Fictional institutions used only to populate the local demo workspace.
    institutions_data = [
        ("Verma Institute of Technology", "South"),
        ("Apex College of Engineering", "West"),
        ("Blue Horizon School of Design", "North"),
        ("Nirmala Polytechnic College", "East"),
        ("Global Heights Technical Campus", "Central"),
        ("Lords Institute of Management", "South"),
        ("Aravalli Institute of Applied Sciences", "North"),
        ("Satpura School of Engineering", "Central"),
        ("Konkan Institute of Digital Systems", "West"),
        ("Deccan Valley College of Technology", "South"),
        ("Eastgate Institute of Design and Technology", "East"),
        ("Northstar Institute of Engineering", "North"),
        ("Western Ghats Institute of Management", "West"),
        ("Central Plains Polytechnic", "Central"),
        ("Delta Coast School of Computing", "East"),
    ]
    inst_by_name: dict[str, models.Institution] = {}
    for name, region in institutions_data:
        inst = db.query(models.Institution).filter_by(name=name).first()
        if inst is None:
            inst = models.Institution(name=name, region=region)
            db.add(inst)
            db.flush()
        inst_by_name[name] = inst

    # Demo accounts provide a reviewer for each region and each workflow role.
    password_hash: str | None = None
    users_data = [
        # (email, full_name, role, region, institution_name_or_None)
        ("admin@nexora-demo.in", "Aarav Admin", "admin", None, None),
        ("institution@nexora-demo.in", "Dr. Tara Institution", "institution",
         "South", "Verma Institute of Technology"),
        ("regional@nexora-demo.in", "Rohan Regional", "regional_officer",
         "South", None),
        ("north.regional@nexora-demo.in", "Nisha North", "regional_officer",
         "North", None),
        ("east.regional@nexora-demo.in", "Esha East", "regional_officer",
         "East", None),
        ("west.regional@nexora-demo.in", "Varun West", "regional_officer",
         "West", None),
        ("central.regional@nexora-demo.in", "Chetan Central", "regional_officer",
         "Central", None),
        ("bureau@nexora-demo.in", "Bina Bureau", "bureau_officer", None, None),
        ("evc@nexora-demo.in", "Eshan EVC", "evc_committee", None, None),
    ]
    for email, full_name, role, region, inst_name in users_data:
        if db.query(models.User).filter_by(email=email).first():
            continue
        if password_hash is None:
            password_hash = hash_password(DEMO_PASSWORD)
        institution_id = inst_by_name[inst_name].id if inst_name else None
        db.add(models.User(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            role=role,
            region=region,
            institution_id=institution_id,
            is_active=True,
        ))

    for category in DOCUMENT_CATEGORIES:
        if db.query(models.DocumentCategory).filter_by(name=category).first() is None:
            db.add(models.DocumentCategory(name=category))
    db.flush()
    users = {user.email: user for user in db.query(models.User).all()}
    institutions = {institution.name: institution for institution in db.query(models.Institution).all()}
    now = datetime.utcnow()
    # A varied, internally linked portfolio for demonstrating filters, queues,
    # history, review outcomes and deadlines. These are synthetic demo records.
    scenarios = [
        ("APP-2026-0001", "Verma Institute of Technology", "New Institution", "initial_scrutiny", "pending", 18, 12, "Medium"),
        ("APP-2026-0002", "Blue Horizon School of Design", "Program Expansion", "deficiency_check", "returned", 27, 4, "High"),
        ("APP-2026-0003", "Apex College of Engineering", "New Institution", "evc_scheduling", "pending", 35, 18, "High"),
        ("APP-2026-0004", "Verma Institute of Technology", "Renewal", "initial_scrutiny", "pending", 42, -4, "High"),
        ("APP-2026-0005", "Nirmala Polytechnic College", "Program Expansion", "final_status", "approved", 74, None, "Low"),
        ("APP-2026-0006", "Aravalli Institute of Applied Sciences", "New Institution", "initial_scrutiny", "pending", 9, 19, "Medium"),
        ("APP-2026-0007", "Konkan Institute of Digital Systems", "Increase in Approved Intake", "evc_scheduling", "pending", 58, 11, "High"),
        ("APP-2026-0008", "Eastgate Institute of Design and Technology", "New Course", "deficiency_check", "returned", 31, 2, "High"),
        ("APP-2026-0009", "Global Heights Technical Campus", "Change of Institution Name", "committee_stage", "pending", 86, 21, "Medium"),
        ("APP-2026-0010", "Deccan Valley College of Technology", "Renewal", "final_status", "rejected", 113, None, "Low"),
        ("APP-2026-0011", "Northstar Institute of Engineering", "Program Expansion", "final_status", "approved", 126, None, "Low"),
        ("APP-2026-0012", "Western Ghats Institute of Management", "New Institution", "initial_scrutiny", "pending", 6, 24, "Medium"),
        ("APP-2026-0013", "Delta Coast School of Computing", "New Course", "evc_completion", "pending", 67, 9, "High"),
        ("APP-2026-0014", "Central Plains Polytechnic", "Increase in Approved Intake", "deficiency_check", "returned", 45, -2, "High"),
        ("APP-2026-0015", "Lords Institute of Management", "Program Expansion", "committee_stage", "pending", 96, 16, "Medium"),
        ("APP-2026-0016", "Blue Horizon School of Design", "Renewal", "evc_scheduling", "pending", 52, 14, "High"),
        ("APP-2026-0017", "Konkan Institute of Digital Systems", "New Course", "final_status", "approved", 102, None, "Low"),
        ("APP-2026-0018", "Nirmala Polytechnic College", "Program Expansion", "initial_scrutiny", "pending", 14, 22, "Medium"),
        ("APP-2026-0019", "Satpura School of Engineering", "New Institution", "final_status", "approved", 149, None, "Low"),
        ("APP-2026-0020", "Verma Institute of Technology", "Increase in Approved Intake", "deficiency_check", "pending", 23, 7, "High"),
        ("APP-2026-0021", "Aravalli Institute of Applied Sciences", "New Course", "committee_stage", "pending", 81, 13, "Medium"),
        ("APP-2026-0022", "Western Ghats Institute of Management", "Renewal", "evc_completion", "pending", 61, 5, "High"),
        ("APP-2026-0023", "Eastgate Institute of Design and Technology", "Program Expansion", "final_status", "rejected", 132, None, "Low"),
        ("APP-2026-0024", "Central Plains Polytechnic", "New Course", "evc_scheduling", "pending", 39, 17, "Medium"),
        ("APP-2026-0025", "Deccan Valley College of Technology", "Program Expansion", "initial_scrutiny", "pending", 11, 20, "Medium"),
    ]
    stage_names = {
        rule.stage_key: rule.stage_name
        for rule in db.query(models.WorkflowRules).all()
    }
    officers = {
        user.region: user
        for user in db.query(models.User).filter_by(role="regional_officer").all()
    }
    stage_order = [rule[0] for rule in workflow_rules]
    applications_by_id: dict[str, models.Application] = {}
    for app_id, institution_name, app_type, stage, status, submitted_days, deadline_days, priority in scenarios:
        institution = institutions[institution_name]
        officer = officers.get(institution.region)
        application = db.query(models.Application).filter_by(id=app_id).first()
        if application is None:
            submitted_at = now - timedelta(days=submitted_days)
            application = models.Application(
                id=app_id, institution_id=institution.id, region=institution.region,
                application_type=app_type, submitted_at=submitted_at, current_stage=stage,
                status=status, assigned_officer_id=officer.id if officer else None,
                deadline=now + timedelta(days=deadline_days) if deadline_days is not None else None,
                priority=priority, scenario_tag="synthetic_demo",
            )
            db.add(application)
            db.flush()
        elif application.assigned_officer_id is None and officer is not None:
            application.assigned_officer_id = officer.id
        applications_by_id[app_id] = application

        # Fill missing history for seeded cases without overwriting user changes.
        if application.current_stage != stage or application.status != status:
            continue
        current_index = stage_order.index(stage)
        path = stage_order[:current_index + 1]
        existing_stage_keys = {
            row.stage_key for row in db.query(models.ApplicationStage)
            .filter_by(application_id=app_id).all()
        }
        actor_id = officer.id if officer else users["admin@nexora-demo.in"].id
        for index, stage_key in enumerate(path):
            if stage_key in existing_stage_keys:
                continue
            elapsed = submitted_days - round(submitted_days * index / max(len(path) - 1, 1))
            entered_at = now - timedelta(days=max(elapsed, 0))
            is_current = stage_key == stage
            stage_status = (
                "returned" if is_current and status == "returned"
                else "active" if is_current and status not in {"approved", "rejected"}
                else "completed"
            )
            db.add(models.ApplicationStage(
                application_id=app_id, stage_key=stage_key,
                stage_name=stage_names.get(stage_key, stage_key),
                entered_at=entered_at,
                exited_at=now - timedelta(days=max(elapsed - 1, 0)) if not is_current else None,
                actor_user_id=actor_id, status=stage_status,
                reason="Synthetic demo workflow history",
            ))
        applications_by_id[app_id] = application
    db.flush()

    observation_examples = [
        ("APP-2026-0002", "Please provide the revised semester-wise faculty deployment statement.", "medium"),
        ("APP-2026-0008", "The submitted programme nomenclature differs from the application form; please reconcile both records.", "high"),
        ("APP-2026-0014", "Provide a signed explanation for the requested intake increase and revised infrastructure schedule.", "high"),
        ("APP-2026-0020", "Upload the updated laboratory utilization statement for the proposed additional intake.", "medium"),
    ]
    for app_id, text, severity in observation_examples:
        if db.query(models.ScrutinyObservations).filter_by(
            application_id=app_id, observation_text=text
        ).first() is None:
            application = applications_by_id[app_id]
            officer = officers.get(application.region)
            db.add(models.ScrutinyObservations(
                application_id=app_id, officer_id=officer.id if officer else users["admin@nexora-demo.in"].id,
                observation_text=text, is_deficiency=True, severity=severity,
                created_at=now - timedelta(days=5),
            ))
    db.flush()

    evc_examples = [
        ("APP-2026-0003", 9, "South Regional Review Centre", "scheduled", None, None),
        ("APP-2026-0007", 12, "West Regional Review Centre", "scheduled", None, None),
        ("APP-2026-0013", -6, "East Regional Review Centre", "completed", "Facilities and records were reviewed against the submitted application.", "Recommended"),
        ("APP-2026-0016", 16, "North Regional Review Centre", "scheduled", None, None),
        ("APP-2026-0017", -24, "West Regional Review Centre", "completed", "Visit observations were recorded and supporting documents were found consistent.", "Recommended"),
        ("APP-2026-0022", -3, "West Regional Review Centre", "completed", "Additional evidence was requested for one programme; remaining records were reviewed.", "Conditional Recommendation"),
        ("APP-2026-0024", 21, "Central Regional Review Centre", "scheduled", None, None),
    ]
    for app_id, day_offset, location, status, findings, recommendation in evc_examples:
        if db.query(models.EVCAppointments).filter_by(application_id=app_id).first():
            continue
        db.add(models.EVCAppointments(
            application_id=app_id, scheduled_date=now + timedelta(days=day_offset),
            location=location, committee_members=str(users["evc@nexora-demo.in"].id),
            status=status,
            completed_at=now + timedelta(days=day_offset + 1) if status == "completed" else None,
            completed_by=users["evc@nexora-demo.in"].id if status == "completed" else None,
            findings=findings, recommendation=recommendation,
        ))
    db.flush()

    document_examples = [
        ("APP-2026-0001", "Approval Supporting Documents", "application-summary.pdf", 12, "under_verification", 980_000),
        ("APP-2026-0002", "Compliance Evidence", "faculty-deployment-revision.pdf", 180, "deficient", 640_000),
        ("APP-2026-0003", "Land and Building Documents", "campus-site-plan.pdf", 410, "verified", 1_420_000),
        ("APP-2026-0004", "Lease Documents", "lease-deed-renewal.pdf", -4, "expired", 1_130_000),
        ("APP-2026-0005", "Institutional Undertakings", "undertaking-signed.pdf", 245, "verified", 285_000),
        ("APP-2026-0007", "Approval Supporting Documents", "intake-proposal.pdf", 22, "under_verification", 760_000),
        ("APP-2026-0008", "Compliance Evidence", "programme-correction-note.pdf", 330, "under_verification", 390_000),
        ("APP-2026-0009", "Land and Building Documents", "building-safety-certificate.pdf", 22, "expiring_soon", 515_000),
        ("APP-2026-0011", "Approval Supporting Documents", "approval-record-2025.pdf", 295, "verified", 870_000),
        ("APP-2026-0013", "Other Prescribed Documents", "evc-visit-observations.pdf", 190, "verified", 455_000),
        ("APP-2026-0014", "Compliance Evidence", "laboratory-utilization-statement.pdf", 120, "deficient", 570_000),
        ("APP-2026-0017", "Approval Supporting Documents", "programme-review-record.pdf", 202, "verified", 690_000),
        ("APP-2026-0019", "Land and Building Documents", "occupancy-certificate.pdf", 365, "verified", 740_000),
        ("APP-2026-0020", "Compliance Evidence", "laboratory-inventory-update.pdf", 18, "under_verification", 820_000),
        ("APP-2026-0022", "Lease Documents", "campus-lease-schedule.pdf", 7, "under_verification", 625_000),
        ("APP-2026-0024", "Approval Supporting Documents", "proposed-course-structure.pdf", 24, "uploaded", 490_000),
    ]
    for app_id, category, file_name, expiry_days, status, file_size in document_examples:
        document = db.query(models.Documents).filter_by(file_name=file_name).first()
        if document is None:
            application = applications_by_id[app_id]
            officer = officers.get(application.region)
            document = models.Documents(
                application_id=app_id, institution_id=application.institution_id,
                category=category, file_name=file_name,
                stored_path=f"seeded://demo-evidence/{file_name}",
                mime_type="application/pdf", file_size=file_size,
                uploaded_by=users["institution@nexora-demo.in"].id,
                uploaded_at=now - timedelta(days=7),
                expiry_date=now + timedelta(days=expiry_days),
                status=status,
                verified_by=officer.id if status in {"verified", "deficient"} and officer else None,
                verified_at=now - timedelta(days=2) if status in {"verified", "deficient"} else None,
            )
            db.add(document)
            db.flush()
    db.flush()

    undertaking_examples = [
        ("APP-2026-0001", "Submit annual compliance evidence", 6, "pending", None, None),
        ("APP-2026-0002", "Re-submit corrected faculty deployment statement", 4, "deficient", "Please attach the signed revised statement.", "faculty-deployment-revision.pdf"),
        ("APP-2026-0003", "Provide updated campus safety declaration", 20, "submitted", "Evidence received; review pending.", "campus-site-plan.pdf"),
        ("APP-2026-0004", "Renew campus lease documentation", -3, "overdue", "Updated lease evidence is awaited.", "lease-deed-renewal.pdf"),
        ("APP-2026-0005", "Submit annual institutional undertaking", 55, "verified", "Reviewed and recorded for the demo workflow.", "undertaking-signed.pdf"),
        ("APP-2026-0007", "Provide revised intake utilization statement", 11, "pending", None, None),
        ("APP-2026-0009", "Renew building safety certificate", 28, "pending", None, None),
        ("APP-2026-0011", "Submit annual compliance return", 42, "verified", "Evidence reviewed and accepted in the demo workflow.", "approval-record-2025.pdf"),
        ("APP-2026-0013", "Record visit follow-up evidence", 18, "submitted", "Awaiting officer review.", "evc-visit-observations.pdf"),
        ("APP-2026-0014", "Reconcile laboratory inventory statement", -5, "overdue", "Updated inventory schedule requested.", "laboratory-utilization-statement.pdf"),
        ("APP-2026-0017", "Submit programme review undertaking", 36, "verified", "Review completed in the demo workflow.", "programme-review-record.pdf"),
        ("APP-2026-0019", "Maintain current occupancy documentation", 70, "verified", "Evidence recorded for the current review cycle.", "occupancy-certificate.pdf"),
        ("APP-2026-0020", "Submit updated laboratory inventory", 9, "pending", None, None),
        ("APP-2026-0022", "Provide lease schedule clarification", 5, "submitted", "Clarification received for review.", "campus-lease-schedule.pdf"),
        ("APP-2026-0024", "Submit proposed course documentation", 25, "pending", None, None),
    ]
    for app_id, description, due_days, status, remarks, evidence_name in undertaking_examples:
        if db.query(models.Undertakings).filter_by(
            application_id=app_id, description=description
        ).first():
            continue
        application = applications_by_id[app_id]
        evidence_document = db.query(models.Documents).filter_by(file_name=evidence_name).first() if evidence_name else None
        verified = status == "verified"
        db.add(models.Undertakings(
            application_id=app_id, institution_id=application.institution_id,
            description=description, due_date=now + timedelta(days=due_days),
            submitted_at=now - timedelta(days=2) if status in {"submitted", "verified", "deficient"} else None,
            evidence_document_id=evidence_document.id if evidence_document else None,
            status=status,
            verifying_officer_id=officers.get(application.region).id if verified and officers.get(application.region) else None,
            remarks=remarks,
        ))
    db.flush()

    submission_examples = [
        ("APP-2026-0003", "Annual safety evidence review", 20, "submitted", "campus-site-plan.pdf"),
        ("APP-2026-0004", "Lease renewal evidence review", -3, "overdue", "lease-deed-renewal.pdf"),
        ("APP-2026-0005", "Institutional undertaking review", 55, "verified", "undertaking-signed.pdf"),
        ("APP-2026-0014", "Laboratory inventory evidence review", -5, "deficient", "laboratory-utilization-statement.pdf"),
        ("APP-2026-0022", "Lease schedule evidence review", 5, "submitted", "campus-lease-schedule.pdf"),
    ]
    for app_id, description, due_days, status, evidence_name in submission_examples:
        if db.query(models.ComplianceSubmissions).filter_by(
            application_id=app_id, description=description
        ).first():
            continue
        application = applications_by_id[app_id]
        undertaking = db.query(models.Undertakings).filter_by(
            application_id=app_id
        ).first()
        evidence_document = db.query(models.Documents).filter_by(
            file_name=evidence_name
        ).first()
        officer = officers.get(application.region)
        db.add(models.ComplianceSubmissions(
            institution_id=application.institution_id,
            application_id=app_id,
            undertaking_id=undertaking.id if undertaking else None,
            description=description,
            due_date=now + timedelta(days=due_days),
            submitted_at=now - timedelta(days=2) if status in {"submitted", "verified", "deficient"} else None,
            evidence_document_id=evidence_document.id if evidence_document else None,
            verification_status=status,
            verifying_officer_id=officer.id if status in {"verified", "deficient"} and officer else None,
            remarks="Synthetic demo compliance record",
        ))

    decision_ids = [
        app_id for app_id, _, _, _, status, *_ in scenarios
        if status in {"approved", "rejected"}
    ]
    for app_id in decision_ids:
        application = applications_by_id[app_id]
        if db.query(models.AuditLogs).filter_by(
            action="application_decision_recorded",
            affected_record_type="application",
            affected_record_id=app_id,
        ).first():
            continue
        db.add(models.AuditLogs(
            user_id=application.assigned_officer_id or users["bureau@nexora-demo.in"].id,
            action="application_decision_recorded",
            affected_record_type="application",
            affected_record_id=app_id,
            previous_status="pending",
            updated_status=application.status,
            reason="Synthetic demo decision history",
            workflow_stage="final_status",
            timestamp=application.submitted_at + timedelta(days=30),
        ))
    if db.query(models.Documents).filter_by(file_name="demo-expired-lease.pdf").first() is None:
        expired = models.Documents(
            application_id="APP-2026-0001",
            institution_id=institutions["Verma Institute of Technology"].id,
            category="Lease Documents", file_name="demo-expired-lease.pdf",
            stored_path="seeded://expired-lease", mime_type="application/pdf", file_size=0,
            uploaded_by=users["institution@nexora-demo.in"].id,
            expiry_date=now - timedelta(days=10), status="expired",
        )
        expiring = models.Documents(
            application_id="APP-2026-0001",
            institution_id=institutions["Verma Institute of Technology"].id,
            category="Lease Documents", file_name="demo-expiring-lease.pdf",
            stored_path="seeded://expiring-lease", mime_type="application/pdf", file_size=0,
            uploaded_by=users["institution@nexora-demo.in"].id,
            expiry_date=now + timedelta(days=45), status="expiring_soon",
        )
        db.add_all([expired, expiring])
        db.flush()
        db.add(models.Documents(
            application_id=expired.application_id, institution_id=expired.institution_id,
            category=expired.category, file_name="demo-lease-renewal.pdf",
            stored_path="seeded://lease-renewal", mime_type="application/pdf", file_size=0,
            uploaded_by=users["institution@nexora-demo.in"].id,
            replacement_for=expired.id, status="under_verification",
        ))
    if db.query(models.Documents).filter_by(file_name="demo-renewal-awaited.pdf").first() is None:
        db.add(models.Documents(
            application_id="APP-2026-0001",
            institution_id=institutions["Verma Institute of Technology"].id,
            category="Lease Documents", file_name="demo-renewal-awaited.pdf",
            stored_path="seeded://renewal-awaited", mime_type="application/pdf", file_size=0,
            uploaded_by=users["institution@nexora-demo.in"].id,
            expiry_date=now - timedelta(days=20), status="expired",
        ))
    db.commit()
