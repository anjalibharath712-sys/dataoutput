from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ebv import process_ebv_benefits
from main import (
    active_payers,
    claims_by_status,
    create_claim,
    create_drug,
    create_patient,
    create_payer,
    create_provider,
    delete_claim,
    delete_drug,
    delete_patient,
    delete_payer,
    delete_provider,
    get_claim,
    get_drug,
    get_patient,
    get_payer,
    get_provider,
    list_claims,
    list_drugs,
    list_patients,
    list_payers,
    list_providers,
    search_drugs,
    search_patients,
    search_providers,
    update_claim,
    update_drug,
    update_patient,
    update_payer,
    update_provider,
    validate_payload,
)

router = APIRouter(prefix="/mcp", tags=["MCP"])

VALID_ACTIONS = {
    "list_patients",
    "get_patient",
    "create_patient",
    "update_patient",
    "delete_patient",
    "search_patients",
    "list_providers",
    "get_provider",
    "create_provider",
    "update_provider",
    "delete_provider",
    "search_providers",
    "list_payers",
    "get_payer",
    "create_payer",
    "update_payer",
    "delete_payer",
    "active_payers",
    "list_drugs",
    "get_drug",
    "create_drug",
    "update_drug",
    "delete_drug",
    "search_drugs",
    "list_claims",
    "get_claim",
    "create_claim",
    "update_claim",
    "delete_claim",
    "claims_by_status",
    "benefits_check",
}

INTENT_ROUTE_MAP = {
    action: action for action in VALID_ACTIONS
}

INTENT_ROUTE_MAP.update({
    "benefits_check": "benefits_check",
    "check_benefits": "benefits_check",
    "covered_pa_required": "benefits_check",
    "covered_step_therapy": "benefits_check",
    "covered_no_restrictions": "benefits_check",
    "not_covered_alternative": "benefits_check",
    "no_active_coverage": "benefits_check",
    "coverage_gap": "benefits_check",
    "payer_timeout": "benefits_check",
})


class MCPRequest(BaseModel):
    intent: str
    payload: Dict[str, Any] = {}


def execute_operation(operation: str, payload: Dict[str, Any]) -> Any:
    if operation == "list_patients":
        return list_patients(limit=payload.get("limit", 100), offset=payload.get("offset", 0))
    if operation == "get_patient":
        validate_payload(payload, ["patientId"])
        return get_patient(payload["patientId"])
    if operation == "create_patient":
        validate_payload(payload, ["patientId", "name", "dob", "gender", "payerId"])
        return create_patient(payload)
    if operation == "update_patient":
        validate_payload(payload, ["patientId"])
        return update_patient(payload["patientId"], payload)
    if operation == "delete_patient":
        validate_payload(payload, ["patientId"])
        return delete_patient(payload["patientId"])
    if operation == "search_patients":
        return search_patients(name=payload.get("name"), payerId=payload.get("payerId"))
    if operation == "list_providers":
        return list_providers(limit=payload.get("limit", 100), offset=payload.get("offset", 0))
    if operation == "get_provider":
        validate_payload(payload, ["providerId"])
        return get_provider(payload["providerId"])
    if operation == "create_provider":
        validate_payload(payload, ["providerId", "npi", "name", "specialty", "phone"])
        return create_provider(payload)
    if operation == "update_provider":
        validate_payload(payload, ["providerId"])
        return update_provider(payload["providerId"], payload)
    if operation == "delete_provider":
        validate_payload(payload, ["providerId"])
        return delete_provider(payload["providerId"])
    if operation == "search_providers":
        return search_providers(name=payload.get("name"), specialty=payload.get("specialty"))
    if operation == "list_payers":
        return list_payers(limit=payload.get("limit", 100), offset=payload.get("offset", 0))
    if operation == "get_payer":
        validate_payload(payload, ["payerId"])
        return get_payer(payload["payerId"])
    if operation == "create_payer":
        validate_payload(payload, ["payerId", "name", "planName"])
        return create_payer(payload)
    if operation == "update_payer":
        validate_payload(payload, ["payerId"])
        return update_payer(payload["payerId"], payload)
    if operation == "delete_payer":
        validate_payload(payload, ["payerId"])
        return delete_payer(payload["payerId"])
    if operation == "active_payers":
        return active_payers()
    if operation == "list_drugs":
        return list_drugs(limit=payload.get("limit", 100), offset=payload.get("offset", 0))
    if operation == "get_drug":
        validate_payload(payload, ["drugNdc"])
        return get_drug(payload["drugNdc"])
    if operation == "create_drug":
        validate_payload(payload, ["drugNdc", "name", "strength", "form", "copay"])
        return create_drug(payload)
    if operation == "update_drug":
        validate_payload(payload, ["drugNdc"])
        return update_drug(payload["drugNdc"], payload)
    if operation == "delete_drug":
        validate_payload(payload, ["drugNdc"])
        return delete_drug(payload["drugNdc"])
    if operation == "search_drugs":
        return search_drugs(name=payload.get("name"), strength=payload.get("strength"))
    if operation == "benefits_check":
        validate_payload(payload, ["npi", "patientId", "patientDob", "drugNdc"])
        return process_ebv_benefits(payload, payload.get("scenario"), payload.get("authorization"))
    if operation == "list_claims":
        return list_claims(limit=payload.get("limit", 100), offset=payload.get("offset", 0))
    if operation == "get_claim":
        validate_payload(payload, ["claimId"])
        return get_claim(int(payload["claimId"]))
    if operation == "create_claim":
        validate_payload(payload, ["patientId", "providerId", "drugNdc", "amount", "status", "submittedAt"])
        return create_claim(payload)
    if operation == "update_claim":
        validate_payload(payload, ["claimId"])
        return update_claim(int(payload["claimId"]), payload)
    if operation == "delete_claim":
        validate_payload(payload, ["claimId"])
        return delete_claim(int(payload["claimId"]))
    if operation == "claims_by_status":
        validate_payload(payload, ["status"])
        return claims_by_status(payload["status"])
    raise HTTPException(status_code=400, detail={"error": "invalid_intent", "message": f"Unknown intent: {operation}"})


@router.post("/request")
def mcp_request(request: MCPRequest):
    intent = request.intent.strip().lower()
    if intent not in INTENT_ROUTE_MAP:
        raise HTTPException(status_code=400, detail={"error": "unknown_intent", "message": f"Unknown intent: {intent}"})
    operation = INTENT_ROUTE_MAP[intent]
    result = execute_operation(operation, request.payload)
    return {"success": True, "intent": intent, "operation": operation, "result": result}


@router.post("/route/{operation}")
def mcp_route(operation: str, payload: Dict[str, Any]):
    if operation not in VALID_ACTIONS:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": f"Operation {operation} is not available."})
    result = execute_operation(operation, payload)
    return {"success": True, "operation": operation, "result": result}


@router.get("/routes")
def mcp_routes():
    return {"available_routes": sorted(list(VALID_ACTIONS))}

mcp_router = router
