from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models import User, WorkflowRules
from app.services.audit import log_action
from app.workflow_paths import WORKFLOW_PATHS, suggest_workflow_path

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


class RuleUpdate(BaseModel):
    requires_scrutiny: bool | None = None
    requires_evc: bool | None = None
    requires_committee: bool | None = None
    deadline_days: int | None = None
    allowed_roles: str | None = None
    is_active: bool | None = None


class WorkflowSuggestionRequest(BaseModel):
    application_type: str = Field(min_length=2, max_length=100)


@router.get("/paths")
def list_paths(user: User = Depends(get_current_user)):
    return [
        {
            "key": key,
            "label": path["label"],
            "description": path["description"],
            "stages": list(path["stages"]),
            "is_demo_example": True,
        }
        for key, path in WORKFLOW_PATHS.items()
    ]


@router.post("/suggest")
def suggest_path(
    payload: WorkflowSuggestionRequest,
    user: User = Depends(get_current_user),
):
    path_key, reason = suggest_workflow_path(payload.application_type)
    path = WORKFLOW_PATHS[path_key]
    return {
        "key": path_key,
        "label": path["label"],
        "description": path["description"],
        "reason": reason,
        "is_demo_suggestion": True,
    }


@router.get("/rules")
def list_rules(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(WorkflowRules).order_by(WorkflowRules.stage_order).all()


@router.put("/rules/{stage_key}")
def update_rule(stage_key: str, payload: RuleUpdate, db: Session = Depends(get_db),
                admin: User = Depends(require_admin)):
    rule = db.query(WorkflowRules).filter_by(stage_key=stage_key).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Workflow rule not found")
    if payload.deadline_days is not None and payload.deadline_days < 0:
        raise HTTPException(status_code=400, detail="deadline_days cannot be negative")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    log_action(db, admin, "workflow_rule_updated", "workflow_rule", stage_key)
    db.commit()
    db.refresh(rule)
    return rule
