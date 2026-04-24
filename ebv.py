from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/ebv", tags=["EBV"])

REQUIRED_FIELDS = ["npi", "patientId", "patientDob", "drugNdc"]


class EBVRequest(BaseModel):
    payload: Dict[str, Any] = Field(...)


def validate_ebv_payload(payload: Dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in payload or payload[field] in (None, "")]
    if missing:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "validation_failed",
                "missingFields": missing,
                "message": "Required EBV payload fields are missing.",
            },
        )


def get_scenario_response(scenario: str) -> Dict[str, Any]:
    scenario = scenario.strip().lower()
    responses = {
        "covered_no_restrictions": {
            "covered": True,
            "restrictions": "none",
            "message": "Covered with no restrictions.",
        },
        "covered_pa_required": {
            "covered": True,
            "requiresPriorAuth": True,
            "message": "Covered but prior authorization is required.",
        },
        "covered_step_therapy": {
            "covered": True,
            "requiresStepTherapy": True,
            "message": "Covered with step therapy requirement.",
        },
        "not_covered_alternative": {
            "covered": False,
            "alternatives": ["Alternative Drug A", "Alternative Drug B"],
            "message": "Not covered. Suggested alternatives are provided.",
        },
        "no_active_coverage": {
            "covered": False,
            "message": "No active coverage found for this patient.",
        },
        "coverage_gap": {
            "covered": False,
            "message": "Coverage gap detected. The patient may not be covered for this service.",
        },
    }
    return responses.get(
        scenario,
        {
            "covered": True,
            "requiresPriorAuth": True,
            "message": "Default benefits response: covered but prior authorization is required.",
        },
    )


def process_ebv_benefits(payload: Dict[str, Any], scenario: Optional[str] = None, authorization: Optional[str] = None) -> Dict[str, Any]:
    if authorization is None:
        raise HTTPException(status_code=401, detail={"error": "unauthorized", "message": "Missing Authorization header."})
    validate_ebv_payload(payload)
    if not isinstance(payload, dict) or not payload:
        raise HTTPException(status_code=400, detail={"error": "empty_body", "message": "Request body is empty."})
    chosen_scenario = scenario or "covered_pa_required"
    if chosen_scenario.strip().lower() == "payer_timeout":
        raise HTTPException(status_code=504, detail={"error": "payer_timeout", "message": "Simulated payer timeout."})
    return {
        "success": True,
        "scenario": chosen_scenario,
        "requestPayload": payload,
        "result": get_scenario_response(chosen_scenario),
    }


@router.post("/benefits")
def ebv_benefits(request: EBVRequest, x_scenario: Optional[str] = Header("covered_pa_required", alias="x-scenario"), authorization: Optional[str] = Header(None, alias="Authorization")):
    return process_ebv_benefits(request.payload, x_scenario, authorization)


ebv_router = router
