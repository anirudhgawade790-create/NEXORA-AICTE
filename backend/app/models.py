"""SQLAlchemy models for NEXORA AICTE -- the full 14-table relational schema.

Enum-like values are stored as String columns with CHECK constraints so the
allowed states are enforced at the DB level and the schema stays portable.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    region = Column(String(50), nullable=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "role IN ('institution','regional_officer','bureau_officer','evc_committee','admin')",
            name="ck_users_role",
        ),
    )


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    region = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class Application(Base):
    __tablename__ = "applications"

    id = Column(String(32), primary_key=True)  # 'APP-YYYY-NNNN'
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    region = Column(String(50), index=True, nullable=False)
    application_type = Column(String(100), nullable=False)
    submitted_at = Column(DateTime, index=True, nullable=False, default=func.now())
    current_stage = Column(String(50), nullable=False)
    status = Column(String(50), index=True, nullable=False)
    assigned_officer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    deadline = Column(DateTime, nullable=True)
    priority = Column(String(20), nullable=False, default="Medium")
    scenario_tag = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class ApplicationStage(Base):
    __tablename__ = "application_stages"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String(32), ForeignKey("applications.id"), index=True, nullable=False)
    stage_key = Column(String(50), nullable=False)
    stage_name = Column(String(100), nullable=False)
    entered_at = Column(DateTime, nullable=False, default=func.now())
    exited_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="active")
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('active','completed','returned')", name="ck_application_stages_status"
        ),
    )


class WorkflowRules(Base):
    __tablename__ = "workflow_rules"

    id = Column(Integer, primary_key=True, index=True)
    stage_key = Column(String(50), unique=True, index=True, nullable=False)
    stage_name = Column(String(100), nullable=False)
    stage_order = Column(Integer, nullable=False)
    requires_scrutiny = Column(Boolean, default=False, nullable=False)
    requires_evc = Column(Boolean, default=False, nullable=False)
    requires_committee = Column(Boolean, default=False, nullable=False)
    allowed_roles = Column(String(255), nullable=False)  # comma-separated role list
    deadline_days = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class ScrutinyObservations(Base):
    __tablename__ = "scrutiny_observations"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String(32), ForeignKey("applications.id"), index=True, nullable=False)
    officer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    observation_text = Column(Text, nullable=False)
    is_deficiency = Column(Boolean, default=False, nullable=False)
    severity = Column(String(20), nullable=False, default="low")
    created_at = Column(DateTime, default=func.now(), nullable=False)


class Documents(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String(32), ForeignKey("applications.id"), nullable=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), index=True, nullable=True)
    category = Column(String(100), nullable=False)
    file_name = Column(String(255), nullable=False)
    stored_path = Column(String(512), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=func.now(), nullable=False)
    expiry_date = Column(DateTime, index=True, nullable=True)
    ocr_text = Column(Text, nullable=True)
    status = Column(String(30), index=True, nullable=False, default="uploaded")
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    replacement_for = Column(Integer, ForeignKey("documents.id"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('uploaded','under_verification','verified','deficient',"
            "'rejected','expiring_soon','expired')",
            name="ck_documents_status",
        ),
    )


class DocumentVerifications(Base):
    __tablename__ = "document_verifications"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    verifier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(30), nullable=False)
    remarks = Column(Text, nullable=True)
    is_ocr_attempted = Column(Boolean, default=False, nullable=False)
    ocr_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class EVCAppointments(Base):
    __tablename__ = "evc_appointments"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String(32), ForeignKey("applications.id"), index=True, nullable=False)
    scheduled_date = Column(DateTime, index=True, nullable=False)
    location = Column(String(255), nullable=False)
    committee_members = Column(Text, nullable=True)  # JSON-serialized user id list
    status = Column(String(20), index=True, nullable=False, default="scheduled")
    completed_at = Column(DateTime, nullable=True)
    completed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    findings = Column(Text, nullable=True)
    recommendation = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled','completed','cancelled')", name="ck_evc_appointments_status"
        ),
    )


class Undertakings(Base):
    __tablename__ = "undertakings"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String(32), ForeignKey("applications.id"), nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id"), index=True, nullable=False)
    description = Column(Text, nullable=False)
    due_date = Column(DateTime, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    evidence_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    status = Column(String(20), index=True, nullable=False, default="pending")
    verifying_officer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','submitted','verified','deficient','overdue')",
            name="ck_undertakings_status",
        ),
    )


class ComplianceSubmissions(Base):
    __tablename__ = "compliance_submissions"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), index=True, nullable=False)
    application_id = Column(String(32), ForeignKey("applications.id"), nullable=True)
    undertaking_id = Column(Integer, ForeignKey("undertakings.id"), nullable=True)
    description = Column(Text, nullable=False)
    due_date = Column(DateTime, index=True, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    evidence_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    verification_status = Column(String(20), index=True, nullable=False, default="pending")
    verifying_officer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('pending','submitted','verified','deficient','overdue')",
            name="ck_compliance_submissions_verification_status",
        ),
    )


class Notifications(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False)
    related_id = Column(String(64), nullable=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, index=True, nullable=False, default=func.now())
    due_date = Column(DateTime, nullable=True)
    is_read = Column(Boolean, default=False, index=True, nullable=False)
    action_link = Column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_notifications_recipient_read", "recipient_id", "is_read"),
    )


class Escalations(Base):
    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String(32), ForeignKey("applications.id"), nullable=True)
    compliance_id = Column(Integer, ForeignKey("compliance_submissions.id"), nullable=True)
    level = Column(Integer, nullable=False, default=1)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    resolved = Column(Boolean, default=False, nullable=False)


class AuditLogs(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    affected_record_type = Column(String(50), nullable=False)
    affected_record_id = Column(String(64), nullable=False)
    previous_status = Column(String(50), nullable=True)
    updated_status = Column(String(50), nullable=True)
    reason = Column(Text, nullable=True)
    workflow_stage = Column(String(50), nullable=True)
    timestamp = Column(DateTime, index=True, nullable=False, default=func.now())


class DocumentCategory(Base):
    __tablename__ = "document_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class SystemConfig(Base):
    __tablename__ = "system_config"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
