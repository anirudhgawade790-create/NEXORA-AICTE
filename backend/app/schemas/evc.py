from datetime import datetime

from pydantic import BaseModel, Field


class EVCAppointmentCreate(BaseModel):
    application_id: str
    scheduled_date: datetime
    location: str = Field(min_length=2)
    committee_members: list[int] = Field(default_factory=list)


class EVCCompletion(BaseModel):
    findings: str = Field(min_length=2)
    recommendation: str = Field(min_length=2)
