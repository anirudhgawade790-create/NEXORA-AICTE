WORKFLOW_PATHS = {
    "scrutiny_only": {
        "label": "Only Scrutiny",
        "description": "Scrutiny and deficiency review, followed by the authorised decision stages.",
        "stages": (
            "submission",
            "initial_scrutiny",
            "deficiency_check",
            "authorised_decision",
            "final_status",
        ),
    },
    "scrutiny_evc": {
        "label": "Scrutiny + EVC",
        "description": "Scrutiny, EVC scheduling/completion, then the authorised decision stages.",
        "stages": (
            "submission",
            "initial_scrutiny",
            "deficiency_check",
            "evc_scheduling",
            "evc_completion",
            "authorised_decision",
            "final_status",
        ),
    },
    "evc_sac_shc": {
        "label": "EVC + SAC/SHC",
        "description": "EVC scheduling/completion, committee review, then the authorised decision stages.",
        "stages": (
            "submission",
            "evc_scheduling",
            "evc_completion",
            "committee_stage",
            "authorised_decision",
            "final_status",
        ),
    },
    "scrutiny_evc_sac_shc": {
        "label": "Scrutiny + EVC + SAC/SHC",
        "description": "Scrutiny, EVC, committee review, then the authorised decision stages.",
        "stages": (
            "submission",
            "initial_scrutiny",
            "deficiency_check",
            "evc_scheduling",
            "evc_completion",
            "committee_stage",
            "authorised_decision",
            "final_status",
        ),
    },
    "only_evc": {
        "label": "Only EVC",
        "description": "EVC scheduling/completion, followed by the authorised decision stages.",
        "stages": (
            "submission",
            "evc_scheduling",
            "evc_completion",
            "authorised_decision",
            "final_status",
        ),
    },
}

DEFAULT_WORKFLOW_PATH = "scrutiny_evc_sac_shc"


def suggest_workflow_path(application_type: str) -> tuple[str, str]:
    """Suggest an illustrative route from common demo application labels."""
    normalized = " ".join(application_type.casefold().replace("-", " ").split())
    if any(term in normalized for term in ("new institution", "new technical institution")):
        return "scrutiny_evc_sac_shc", "New-institution demo scenario: scrutiny, EVC and committee review."
    if any(term in normalized for term in ("renewal", "extension of approval", "change of name", "name change")):
        return "scrutiny_only", "Renewal/change demo scenario: scrutiny-only route."
    if any(term in normalized for term in ("program expansion", "programme expansion", "new course", "increase in intake")):
        return "scrutiny_evc", "Expansion demo scenario: scrutiny and EVC route."
    if any(term in normalized for term in ("sac", "shc", "committee")):
        return "evc_sac_shc", "Committee demo scenario: EVC followed by committee review."
    if "evc" in normalized:
        return "only_evc", "EVC demo scenario: EVC-only route."
    return DEFAULT_WORKFLOW_PATH, "No matching demo rule; suggested the full example route. You can change it."
