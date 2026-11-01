"""Idempotent reference + demo seed data for the NEXORA AICTE prototype.

All names are fictional. The shared demo password is documented in the README.
seed_demo_data is only called from init_db() when the users table is empty, so
running it twice (or restarting) does not duplicate rows.
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

    # Six fictional institutions across the five regions.
    institutions_data = [
        ("Verma Institute of Technology", "South"),
        ("Apex College of Engineering", "West"),
        ("Blue Horizon School of Design", "North"),
        ("Nirmala Polytechnic College", "East"),
        ("Global Heights Technical Campus", "Central"),
        ("Lords Institute of Management", "South"),
    ]
    inst_by_name: dict[str, models.Institution] = {}
    for name, region in institutions_data:
        inst = db.query(models.Institution).filter_by(name=name).first()
        if inst is None:
            inst = models.Institution(name=name, region=region)
            db.add(inst)
            db.flush()
        inst_by_name[name] = inst

    # Five demo users, one per role, all fictional. Shared dev password.
    password_hash = hash_password(DEMO_PASSWORD)
    users_data = [
        # (email, full_name, role, region, institution_name_or_None)
        ("admin@nexora-demo.in", "Aarav Admin", "admin", None, None),
        ("institution@nexora-demo.in", "Dr. Tara Institution", "institution",
         "South", "Verma Institute of Technology"),
        ("regional@nexora-demo.in", "Rohan Regional", "regional_officer",
         "South", None),
        ("bureau@nexora-demo.in", "Bina Bureau", "bureau_officer", None, None),
        ("evc@nexora-demo.in", "Eshan EVC", "evc_committee", None, None),
    ]
    for email, full_name, role, region, inst_name in users_data:
        if db.query(models.User).filter_by(email=email).first():
            continue
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
    scenarios = [
        ("APP-2026-0001", "Verma Institute of Technology", "New Institution",
         "initial_scrutiny", "pending", 15, "Scenario 1: normal scrutiny"),
        ("APP-2026-0002", "Blue Horizon School of Design", "Program Expansion",
         "deficiency_check", "returned", 3, "Scenario 2: returned for deficiency"),
        ("APP-2026-0003", "Apex College of Engineering", "New Institution",
         "evc_scheduling", "pending", 20, "Scenario 3: awaiting EVC"),
        ("APP-2026-0004", "Verma Institute of Technology", "Renewal",
         "initial_scrutiny", "pending", -4, "Scenario 6: overdue case"),
        ("APP-2026-0005", "Nirmala Polytechnic College", "Program Expansion",
         "final_status", "approved", None, "Scenario: completed decision"),
    ]
    for app_id, institution_name, app_type, stage, status, deadline_offset, scenario in scenarios:
        if db.query(models.Application).filter_by(id=app_id).first():
            continue
        institution = institutions[institution_name]
        officer = db.query(models.User).filter_by(
            role="regional_officer", region=institution.region
        ).first()
        submitted_at = now - timedelta(days=12)
        deadline = now + timedelta(days=deadline_offset) if deadline_offset is not None else None
        application = models.Application(
            id=app_id, institution_id=institution.id, region=institution.region,
            application_type=app_type, submitted_at=submitted_at, current_stage=stage,
            status=status, assigned_officer_id=officer.id if officer else None,
            deadline=deadline, priority="High" if deadline_offset is not None and deadline_offset < 0 else "Medium",
            scenario_tag=scenario,
        )
        db.add(application)
        db.flush()
        rule = db.query(models.WorkflowRules).filter_by(stage_key=stage).first()
        db.add(models.ApplicationStage(
            application_id=application.id, stage_key=stage,
            stage_name=rule.stage_name if rule else stage,
            entered_at=submitted_at, actor_user_id=officer.id if officer else users["admin@nexora-demo.in"].id,
            status="completed" if status == "approved" else ("returned" if status == "returned" else "active"),
            reason=scenario,
        ))
    db.flush()
    if db.query(models.EVCAppointments).filter_by(application_id="APP-2026-0003").first() is None:
        db.add(models.EVCAppointments(
            application_id="APP-2026-0003", scheduled_date=now + timedelta(days=8),
            location="Regional Review Centre", committee_members=str(users["evc@nexora-demo.in"].id),
            status="scheduled",
        ))
    if db.query(models.Undertakings).filter_by(description="Submit annual compliance evidence").first() is None:
        db.add(models.Undertakings(
            application_id="APP-2026-0001",
            institution_id=institutions["Verma Institute of Technology"].id,
            description="Submit annual compliance evidence", due_date=now + timedelta(days=6),
            status="pending",
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
