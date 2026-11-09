"""Versioned AICTE APH 2024-2027 rules used by the NEXORA prototype."""

from copy import deepcopy
from datetime import datetime, timedelta

APH_SOURCE_DOCUMENT = "https://aicte.gov.in/sites/default/files/APH%20Final.pdf"
APH_ACADEMIC_YEAR = "2024-2027"
APH_PROCESS_NOTES = {
    "scrutiny": [
        "AICTE selects committee members through its web-portal-based automated process.",
        "AICTE Regulation Bureau informs the institution and experts of the date and time.",
        "Two authorized applicant representatives present the application and supporting documents.",
        "Deficiencies are communicated through the AICTE Web-Portal.",
        "Re-Scrutiny verifies only deficiencies identified by Scrutiny.",
        "Scrutiny/Re-Scrutiny is normally online; offline mode is only for extraordinary circumstances.",
        "These AICTE portal actions are not performed by NEXORA.",
    ],
    "evc": [
        "AICTE selects EVC members through its portal-based automated process.",
        "EVC verifies infrastructure and facilities physically or online.",
        "EVC is included only for categories whose APH Table 2.3 requires it.",
        "AICTE committee selection and portal notices are not performed by NEXORA.",
    ],
    "approval": [
        "Approval decisions and speaking orders are published on the AICTE Web-Portal.",
        "Institutions download the EoA letter and approved intake through their institution login.",
        "NEXORA only records a decision/order already issued externally; it does not grant approval.",
    ],
}
APH_RULES = {
    "eoa_self_disclosure": {
        "label": "Extension of Approval (Self-Disclosure)",
        "rule_category": "category_1",
        "clauses": ["2.5", "Table 2.2", "Table 2.3", "2.25"],
        "stages": ["submission", "self_disclosure", "processing"],
        "mandatory_steps": ["self_disclosure"],
        "conditional_steps": [],
        "required_documents": ["Annexure-2"],
        "processing_timeline": "As per AICTE Public Notice",
        "ter_charges": "not_applicable_for_self_disclosure_eoa",
        "minimum_core_courses": None,
    },
    "increase_intake_additional_courses": {
        "label": "Increase in Intake / Additional Courses",
        "rule_category": "category_1",
        "clauses": ["2.6", "Table 2.2", "Table 2.3", "1.8", "1.9", "2.25"],
        "stages": ["submission", "initial_scrutiny", "deficiency_check", "evc_scheduling", "evc_completion", "committee_stage", "authorised_decision", "final_status"],
        "mandatory_steps": ["scrutiny", "evc"],
        "conditional_steps": ["re_scrutiny_if_deficiencies", "sac_shc_based_on_previous_processing_outcome"],
        "required_documents": ["Annexure-2"],
        "processing_timeline": "As per AICTE Public Notice",
        "scope_notes": ["Applies to existing institutions seeking increase in intake or additional courses."],
        "ter_charges": "not_specified_by_this_rule",
        "minimum_core_courses": 3,
    },
    "new_programme_level": {
        "label": "Start a New Programme / Level",
        "rule_category": "category_1",
        "clauses": ["2.7", "2.6", "Table 2.2", "Table 2.3", "1.8", "1.9", "2.25"],
        "stages": ["submission", "initial_scrutiny", "deficiency_check", "evc_scheduling", "evc_completion", "committee_stage", "authorised_decision", "final_status"],
        "mandatory_steps": ["scrutiny", "evc"],
        "conditional_steps": ["re_scrutiny_if_deficiencies", "sac_shc_based_on_previous_processing_outcome"],
        "required_documents": ["Annexure-2"],
        "processing_timeline": "As per AICTE Public Notice",
        "scope_notes": ["Existing institutions apply with their existing EoA; new courses under the programme are processed as per Clause 2.6."],
        "ter_charges": "not_specified_by_this_rule",
        "minimum_core_courses": 3,
    },
    "change_institution_name": {
        "label": "Change of Institution Name",
        "rule_category": "category_1",
        "clauses": ["Table 2.2", "Table 2.3", "1.8", "2.25"],
        "stages": ["submission", "initial_scrutiny", "deficiency_check", "authorised_decision", "final_status"],
        "mandatory_steps": ["scrutiny"],
        "conditional_steps": ["re_scrutiny_if_deficiencies"],
        "required_documents": ["Annexure-2"],
        "processing_timeline": "As per AICTE Public Notice",
        "scope_notes": ["Table 2.2 also lists change of affiliating University/Board or type of institution, with the stated handbook exception."],
        "ter_charges": "not_specified_by_this_rule",
        "minimum_core_courses": None,
    },
    "merger_of_institutions": {
        "label": "Merger of Institutions",
        "rule_category": "category_1",
        "clauses": ["Table 2.2", "Table 2.3", "1.8", "1.9", "2.25"],
        "stages": ["submission", "initial_scrutiny", "deficiency_check", "evc_scheduling", "evc_completion", "committee_stage", "authorised_decision", "final_status"],
        "mandatory_steps": ["scrutiny", "evc"],
        "conditional_steps": ["re_scrutiny_if_deficiencies", "sac_shc_based_on_previous_processing_outcome"],
        "required_documents": ["Annexure-2"],
        "processing_timeline": "As per AICTE Public Notice",
        "scope_notes": ["Table 2.2/2.3 merger category is for institutions operating in the same campus/city."],
        "ter_charges": "not_specified_by_this_rule",
        "minimum_core_courses": None,
    },
    "change_site_location": {
        "label": "Change of Site / Location",
        "rule_category": "category_2",
        "clauses": ["Table 2.2", "Table 2.3", "1.8", "1.9", "2.25"],
        "stages": ["submission", "initial_scrutiny", "deficiency_check", "evc_scheduling", "evc_completion", "committee_stage", "authorised_decision", "final_status"],
        "mandatory_steps": ["scrutiny", "evc"],
        "conditional_steps": ["re_scrutiny_if_deficiencies", "sac_shc_based_on_previous_processing_outcome"],
        "required_documents": ["Annexure-2"],
        "processing_timeline": "Year-round",
        "scope_notes": ["The handbook states campus shifting for Change of Site/Location is to be done during vacation time."],
        "ter_charges": "not_specified_by_this_rule",
        "minimum_core_courses": None,
    },
    "closure_institution": {
        "label": "Closure of Institution",
        "rule_category": "category_2",
        "clauses": ["2.21", "Table 2.2", "Table 2.3", "1.8", "2.25"],
        "stages": ["submission", "initial_scrutiny", "deficiency_check", "authorised_decision", "final_status"],
        "mandatory_steps": ["scrutiny"],
        "conditional_steps": ["re_scrutiny_if_deficiencies"],
        "required_documents": ["Annexure-2"],
        "processing_timeline": "Year-round",
        "scope_notes": ["Closure may be progressive or complete; the handbook specifies additional closure conditions and evidence."],
        "ter_charges": "no_TER_charges",
        "minimum_core_courses": None,
    },
    "change_bank_details": {
        "label": "Change of Bank Details",
        "rule_category": "category_2",
        "clauses": ["Table 2.2", "Table 2.3", "1.8", "2.25"],
        "stages": ["submission", "initial_scrutiny", "deficiency_check", "authorised_decision", "final_status"],
        "mandatory_steps": ["scrutiny"],
        "conditional_steps": ["re_scrutiny_if_deficiencies"],
        "required_documents": ["Annexure-2"],
        "processing_timeline": "Year-round",
        "ter_charges": "not_specified_by_this_rule",
        "minimum_core_courses": None,
    },
    "change_trust_name": {
        "label": "Change of Trust / Society / Company Name",
        "rule_category": "category_2",
        "clauses": ["Table 2.2", "Table 2.3", "1.8", "2.25"],
        "stages": ["submission", "initial_scrutiny", "deficiency_check", "authorised_decision", "final_status"],
        "mandatory_steps": ["scrutiny"],
        "conditional_steps": ["re_scrutiny_if_deficiencies"],
        "required_documents": ["Annexure-2"],
        "processing_timeline": "Year-round",
        "ter_charges": "not_specified_by_this_rule",
        "minimum_core_courses": None,
    },
    "closure_programme_course": {
        "label": "Closure of Programme / Course",
        "rule_category": "category_2",
        "clauses": ["Table 2.2", "Table 2.3", "1.8", "2.25"],
        "stages": ["submission", "initial_scrutiny", "deficiency_check", "authorised_decision", "final_status"],
        "mandatory_steps": ["scrutiny"],
        "conditional_steps": ["re_scrutiny_if_deficiencies"],
        "required_documents": ["Annexure-2"],
        "processing_timeline": "Year-round",
        "ter_charges": "not_specified_by_this_rule",
        "minimum_core_courses": None,
    },
    "odl_online_learning": {
        "label": "ODL / Online Learning",
        "rule_category": "category_2",
        "clauses": ["Table 2.2", "Table 2.3", "1.8", "1.9", "2.25"],
        "stages": ["submission", "initial_scrutiny", "deficiency_check", "evc_scheduling", "evc_completion", "committee_stage", "authorised_decision", "final_status"],
        "mandatory_steps": ["scrutiny", "evc"],
        "conditional_steps": ["re_scrutiny_if_deficiencies", "sac_shc_based_on_previous_processing_outcome"],
        "required_documents": ["Annexure-2"],
        "processing_timeline": "Year-round; processed twice a year as per UGC timeline",
        "ter_charges": "not_specified_by_this_rule",
        "minimum_core_courses": None,
    },
}


def workflow_path_for(rule_key: str) -> str:
    return f"aph_{rule_key}"


def decision_stage_for(rule_key: str) -> str:
    return "processing" if rule_key == "eoa_self_disclosure" else "final_status"


APH_WORKFLOW_PATHS = {
    workflow_path_for(key): {
        "label": rule["label"],
        "description": (
            f"APH {APH_ACADEMIC_YEAR}; {', '.join(rule['clauses'])}. "
            "Conditional steps are not automatic determinations."
        ),
        "stages": tuple(rule["stages"]),
    }
    for key, rule in APH_RULES.items()
}


def public_rule(rule_key: str, rule: dict) -> dict:
    clauses = list(rule["clauses"])
    process_notes = []
    if "scrutiny" in rule["mandatory_steps"]:
        process_notes.extend(APH_PROCESS_NOTES["scrutiny"])
    if "evc" in rule["mandatory_steps"]:
        process_notes.extend(APH_PROCESS_NOTES["evc"])
    process_notes.extend(APH_PROCESS_NOTES["approval"])
    return {
        "key": rule_key,
        "workflow_path": workflow_path_for(rule_key),
        **deepcopy(rule),
        "clauses": clauses,
        "clause": ", ".join(clauses),
        "scope_notes": list(rule.get("scope_notes", [])),
        "process_notes": process_notes,
        "source_document": APH_SOURCE_DOCUMENT,
        "academic_year": APH_ACADEMIC_YEAR,
        "effective_status": "verified_for_handbook_period",
    }


def application_rule_metadata(rule_key: str) -> dict:
    rule = APH_RULES[rule_key]
    return {
        **public_rule(rule_key, rule),
        "clauses": list(rule["clauses"]),
        "required_documents": list(rule["required_documents"]),
        "stages": list(rule["stages"]),
    }


def appeal_deadline(uploaded_at: datetime, authority: str | None) -> datetime | None:
    if authority != "executive_committee":
        return None
    return uploaded_at + timedelta(days=7)


def appeal_is_open(uploaded_at: datetime, authority: str | None, now: datetime) -> bool:
    deadline = appeal_deadline(uploaded_at, authority)
    return deadline is not None and now <= deadline
