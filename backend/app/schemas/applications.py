from pydantic import BaseModel, Field


class ApplicationCreate(BaseModel):
    application_type: str = Field(min_length=2, max_length=100)
    workflow_path: str = Field(min_length=2, max_length=50)
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
