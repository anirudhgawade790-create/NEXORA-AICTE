from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ComplianceCreate(BaseModel):
    description: str = Field(min_length=3)
    due_date: datetime
    application_id: str | None = None


class ComplianceVerifyRequest(BaseModel):
    status: str
    remarks: str = Field(min_length=2)


class DeficiencyComplianceSubmit(BaseModel):
    evidence_document_id: int = Field(gt=0)


class DeficiencyComplianceReview(BaseModel):
    status: Literal["verified", "deficient"]
    remarks: str = Field(min_length=2, max_length=2000)
