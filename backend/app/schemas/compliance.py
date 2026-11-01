from datetime import datetime

from pydantic import BaseModel, Field


class ComplianceCreate(BaseModel):
    description: str = Field(min_length=3)
    due_date: datetime
    application_id: str | None = None


class ComplianceVerifyRequest(BaseModel):
    status: str
    remarks: str = Field(min_length=2)
