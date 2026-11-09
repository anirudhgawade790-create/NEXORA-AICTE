from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ApplicationCreate(BaseModel):
    application_type: str = Field(min_length=2, max_length=100)
    workflow_path: str | None = Field(default=None, min_length=2, max_length=50)
    aph_rule_key: str | None = Field(default=None, min_length=2, max_length=64)
    program_area: Literal["engineering_technology", "other"] | None = None
    core_course_count: int | None = Field(default=None, ge=0)
    institution_id: int | None = None


class TransitionRequest(BaseModel):
    action: str
    reason: str | None = None


class ResubmitRequest(BaseModel):
    reason: str | None = None


class ObservationRequest(BaseModel):
    observation_text: str = Field(min_length=2)
    is_deficiency: bool = False
    severity: str = "low"


class DecisionRecordRequest(BaseModel):
    outcome: Literal["approved", "rejected"]
    authority: Literal["executive_committee", "council"]
    uploaded_at: datetime
    evidence_document_id: int = Field(gt=0)
    source_reference: str = Field(min_length=2, max_length=500)


class AppealCreate(BaseModel):
    reason: str = Field(min_length=2, max_length=5000)
