import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from ebv import ebv_router
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

DB_PATH = Path(__file__).parent / "data.db"

app = FastAPI(title="MCP SQLite API Server", version="1.0.0")



class Patient(BaseModel):
    patientId: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    dob: str = Field(..., min_length=6)
    gender: str = Field(..., min_length=1)
    payerId: str = Field(..., min_length=1)


class Provider(BaseModel):
    providerId: str = Field(..., min_length=1)
    npi: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    specialty: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)


class Payer(BaseModel):
    payerId: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    planName: str = Field(..., min_length=1)
    active: bool = True


class Drug(BaseModel):
    drugNdc: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    strength: str = Field(..., min_length=1)
    form: str = Field(..., min_length=1)
    copay: float


class Claim(BaseModel):
    patientId: str = Field(..., min_length=1)
    providerId: str = Field(..., min_length=1)
    drugNdc: str = Field(..., min_length=1)
    amount: float
    status: str = Field(..., min_length=1)
    submittedAt: str = Field(..., min_length=1)


class MCPRequest(BaseModel):
    intent: str
    payload: Dict[str, Any] = {}


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    return dict(row) if row else None


def initialize_db() -> None:
    conn = get_db_connection()
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS patients (patientId TEXT PRIMARY KEY, name TEXT, dob TEXT, gender TEXT, payerId TEXT)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS providers (providerId TEXT PRIMARY KEY, npi TEXT, name TEXT, specialty TEXT, phone TEXT)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS payers (payerId TEXT PRIMARY KEY, name TEXT, planName TEXT, active INTEGER)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS drugs (drugNdc TEXT PRIMARY KEY, name TEXT, strength TEXT, form TEXT, copay REAL)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS claims (claimId INTEGER PRIMARY KEY AUTOINCREMENT, patientId TEXT, providerId TEXT, drugNdc TEXT, amount REAL, status TEXT, submittedAt TEXT)"
        )

        if conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO patients(patientId, name, dob, gender, payerId) VALUES (?, ?, ?, ?, ?)",
                [
                    ("P001", "Alice Johnson", "1980-01-01", "female", "PAY001"),
                    ("P002", "Bob Williams", "1975-07-12", "male", "PAY002"),
                ],
            )

        if conn.execute("SELECT COUNT(*) FROM providers").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO providers(providerId, npi, name, specialty, phone) VALUES (?, ?, ?, ?, ?)",
                [
                    ("PR001", "1234567890", "Health Solutions", "Cardiology", "555-1001"),
                    ("PR002", "0987654321", "WellCare Clinic", "Primary Care", "555-1002"),
                ],
            )

        if conn.execute("SELECT COUNT(*) FROM payers").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO payers(payerId, name, planName, active) VALUES (?, ?, ?, ?)",
                [
                    ("PAY001", "Acme Health", "Gold Plan", 1),
                    ("PAY002", "BetterCare", "Silver Plan", 1),
                ],
            )

        if conn.execute("SELECT COUNT(*) FROM drugs").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO drugs(drugNdc, name, strength, form, copay) VALUES (?, ?, ?, ?, ?)",
                [
                    ("12345-001", "DrugA", "10mg", "tablet", 12.5),
                    ("12345-002", "DrugB", "20mg", "capsule", 8.0),
                ],
            )

        if conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO claims(patientId, providerId, drugNdc, amount, status, submittedAt) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    ("P001", "PR001", "12345-001", 120.0, "submitted", "2026-04-20"),
                    ("P002", "PR002", "12345-002", 80.0, "approved", "2026-04-21"),
                ],
            )
        conn.commit()
    finally:
        conn.close()


@app.on_event("startup")
def startup_event() -> None:
    initialize_db()


def build_update_clause(payload: Dict[str, Any], allowed_fields: List[str]) -> tuple[str, List[Any]]:
    updates = []
    values: List[Any] = []
    for field in allowed_fields:
        if field in payload:
            updates.append(f"{field} = ?")
            value = payload[field]
            if field == "active":
                value = int(bool(value))
            values.append(value)
    return ", ".join(updates), values


def validate_payload(payload: Dict[str, Any], required_fields: List[str]) -> None:
    missing = [field for field in required_fields if field not in payload or payload[field] in (None, "")]
    if missing:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "validation_failed",
                "missingFields": missing,
                "message": "Required payload fields are missing.",
            },
        )


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


@app.post("/mcp/request")
def mcp_request(request: MCPRequest):
    intent = request.intent.strip().lower()
    if intent not in INTENT_ROUTE_MAP:
        raise HTTPException(status_code=400, detail={"error": "unknown_intent", "message": f"Unknown intent: {intent}"})
    operation = INTENT_ROUTE_MAP[intent]
    result = execute_operation(operation, request.payload)
    return {"success": True, "intent": intent, "operation": operation, "result": result}


@app.post("/mcp/route/{operation}")
def mcp_route(operation: str, payload: Dict[str, Any]):
    if operation not in VALID_ACTIONS:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": f"Operation {operation} is not available."})
    result = execute_operation(operation, payload)
    return {"success": True, "operation": operation, "result": result}


@app.get("/mcp/routes")
def mcp_routes():
    return {"available_routes": sorted(list(VALID_ACTIONS))}


@app.get("/patients")
def list_patients(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM patients LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        return {"patients": [dict(row) for row in rows]}
    finally:
        conn.close()


@app.get("/patients/{patient_id}")
def get_patient(patient_id: str):
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM patients WHERE patientId = ?", (patient_id,)).fetchone()
        result = row_to_dict(row)
        if result is None:
            raise HTTPException(status_code=404, detail="Patient not found")
        return result
    finally:
        conn.close()


@app.post("/patients")
def create_patient(payload: Dict[str, Any]):
    data = Patient(**payload)
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO patients(patientId, name, dob, gender, payerId) VALUES (?, ?, ?, ?, ?)",
            (data.patientId, data.name, data.dob, data.gender, data.payerId),
        )
        conn.commit()
        return {"message": "Patient created", "patient": data.dict()}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Patient with this ID already exists")
    finally:
        conn.close()


@app.put("/patients/{patient_id}")
def update_patient(patient_id: str, payload: Dict[str, Any]):
    allowed_columns = ["name", "dob", "gender", "payerId"]
    update_clause, values = build_update_clause(payload, allowed_columns)
    if not update_clause:
        raise HTTPException(status_code=400, detail="No updatable patient fields provided")
    conn = get_db_connection()
    try:
        cursor = conn.execute(f"UPDATE patients SET {update_clause} WHERE patientId = ?", (*values, patient_id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Patient not found")
        return {"message": "Patient updated"}
    finally:
        conn.close()


@app.delete("/patients/{patient_id}")
def delete_patient(patient_id: str):
    conn = get_db_connection()
    try:
        cursor = conn.execute("DELETE FROM patients WHERE patientId = ?", (patient_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Patient not found")
        return {"message": "Patient deleted"}
    finally:
        conn.close()


@app.get("/patients/search")
def search_patients(name: Optional[str] = None, payerId: Optional[str] = None):
    conn = get_db_connection()
    try:
        query = "SELECT * FROM patients"
        filters: List[str] = []
        parameters: List[Any] = []
        if name:
            filters.append("name LIKE ?")
            parameters.append(f"%{name}%")
        if payerId:
            filters.append("payerId = ?")
            parameters.append(payerId)
        if filters:
            query += " WHERE " + " AND ".join(filters)
        rows = conn.execute(query, parameters).fetchall()
        return {"patients": [dict(row) for row in rows]}
    finally:
        conn.close()


@app.get("/providers")
def list_providers(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM providers LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        return {"providers": [dict(row) for row in rows]}
    finally:
        conn.close()


@app.get("/providers/{provider_id}")
def get_provider(provider_id: str):
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM providers WHERE providerId = ?", (provider_id,)).fetchone()
        result = row_to_dict(row)
        if result is None:
            raise HTTPException(status_code=404, detail="Provider not found")
        return result
    finally:
        conn.close()


@app.post("/providers")
def create_provider(payload: Dict[str, Any]):
    data = Provider(**payload)
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO providers(providerId, npi, name, specialty, phone) VALUES (?, ?, ?, ?, ?)",
            (data.providerId, data.npi, data.name, data.specialty, data.phone),
        )
        conn.commit()
        return {"message": "Provider created", "provider": data.dict()}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Provider with this ID already exists")
    finally:
        conn.close()


@app.put("/providers/{provider_id}")
def update_provider(provider_id: str, payload: Dict[str, Any]):
    allowed_columns = ["npi", "name", "specialty", "phone"]
    update_clause, values = build_update_clause(payload, allowed_columns)
    if not update_clause:
        raise HTTPException(status_code=400, detail="No updatable provider fields provided")
    conn = get_db_connection()
    try:
        cursor = conn.execute(f"UPDATE providers SET {update_clause} WHERE providerId = ?", (*values, provider_id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Provider not found")
        return {"message": "Provider updated"}
    finally:
        conn.close()


@app.delete("/providers/{provider_id}")
def delete_provider(provider_id: str):
    conn = get_db_connection()
    try:
        cursor = conn.execute("DELETE FROM providers WHERE providerId = ?", (provider_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Provider not found")
        return {"message": "Provider deleted"}
    finally:
        conn.close()


@app.get("/providers/search")
def search_providers(name: Optional[str] = None, specialty: Optional[str] = None):
    conn = get_db_connection()
    try:
        query = "SELECT * FROM providers"
        filters: List[str] = []
        parameters: List[Any] = []
        if name:
            filters.append("name LIKE ?")
            parameters.append(f"%{name}%")
        if specialty:
            filters.append("specialty LIKE ?")
            parameters.append(f"%{specialty}%")
        if filters:
            query += " WHERE " + " AND ".join(filters)
        rows = conn.execute(query, parameters).fetchall()
        return {"providers": [dict(row) for row in rows]}
    finally:
        conn.close()


@app.get("/payers")
def list_payers(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM payers LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        return {"payers": [dict(row) for row in rows]}
    finally:
        conn.close()


@app.get("/payers/{payer_id}")
def get_payer(payer_id: str):
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM payers WHERE payerId = ?", (payer_id,)).fetchone()
        result = row_to_dict(row)
        if result is None:
            raise HTTPException(status_code=404, detail="Payer not found")
        result["active"] = bool(result["active"])
        return result
    finally:
        conn.close()


@app.post("/payers")
def create_payer(payload: Dict[str, Any]):
    data = Payer(**payload)
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO payers(payerId, name, planName, active) VALUES (?, ?, ?, ?)",
            (data.payerId, data.name, data.planName, int(data.active)),
        )
        conn.commit()
        return {"message": "Payer created", "payer": data.dict()}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Payer with this ID already exists")
    finally:
        conn.close()


@app.put("/payers/{payer_id}")
def update_payer(payer_id: str, payload: Dict[str, Any]):
    allowed_columns = ["name", "planName", "active"]
    update_clause, values = build_update_clause(payload, allowed_columns)
    if not update_clause:
        raise HTTPException(status_code=400, detail="No updatable payer fields provided")
    conn = get_db_connection()
    try:
        cursor = conn.execute(f"UPDATE payers SET {update_clause} WHERE payerId = ?", (*[int(v) if k == "active" else v for k, v in zip(allowed_columns, values) if k in payload], payer_id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Payer not found")
        return {"message": "Payer updated"}
    finally:
        conn.close()


@app.delete("/payers/{payer_id}")
def delete_payer(payer_id: str):
    conn = get_db_connection()
    try:
        cursor = conn.execute("DELETE FROM payers WHERE payerId = ?", (payer_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Payer not found")
        return {"message": "Payer deleted"}
    finally:
        conn.close()


@app.get("/payers/active")
def active_payers():
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM payers WHERE active = 1").fetchall()
        return {"payers": [dict(row) for row in rows]}
    finally:
        conn.close()


@app.get("/drugs")
def list_drugs(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM drugs LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        return {"drugs": [dict(row) for row in rows]}
    finally:
        conn.close()


@app.get("/drugs/{drug_ndc}")
def get_drug(drug_ndc: str):
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM drugs WHERE drugNdc = ?", (drug_ndc,)).fetchone()
        result = row_to_dict(row)
        if result is None:
            raise HTTPException(status_code=404, detail="Drug not found")
        return result
    finally:
        conn.close()


@app.post("/drugs")
def create_drug(payload: Dict[str, Any]):
    data = Drug(**payload)
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO drugs(drugNdc, name, strength, form, copay) VALUES (?, ?, ?, ?, ?)",
            (data.drugNdc, data.name, data.strength, data.form, data.copay),
        )
        conn.commit()
        return {"message": "Drug created", "drug": data.dict()}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Drug with this NDC already exists")
    finally:
        conn.close()


@app.put("/drugs/{drug_ndc}")
def update_drug(drug_ndc: str, payload: Dict[str, Any]):
    allowed_columns = ["name", "strength", "form", "copay"]
    update_clause, values = build_update_clause(payload, allowed_columns)
    if not update_clause:
        raise HTTPException(status_code=400, detail="No updatable drug fields provided")
    conn = get_db_connection()
    try:
        cursor = conn.execute(f"UPDATE drugs SET {update_clause} WHERE drugNdc = ?", (*values, drug_ndc))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Drug not found")
        return {"message": "Drug updated"}
    finally:
        conn.close()


@app.delete("/drugs/{drug_ndc}")
def delete_drug(drug_ndc: str):
    conn = get_db_connection()
    try:
        cursor = conn.execute("DELETE FROM drugs WHERE drugNdc = ?", (drug_ndc,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Drug not found")
        return {"message": "Drug deleted"}
    finally:
        conn.close()


@app.get("/drugs/search")
def search_drugs(name: Optional[str] = None, strength: Optional[str] = None):
    conn = get_db_connection()
    try:
        query = "SELECT * FROM drugs"
        filters: List[str] = []
        parameters: List[Any] = []
        if name:
            filters.append("name LIKE ?")
            parameters.append(f"%{name}%")
        if strength:
            filters.append("strength LIKE ?")
            parameters.append(f"%{strength}%")
        if filters:
            query += " WHERE " + " AND ".join(filters)
        rows = conn.execute(query, parameters).fetchall()
        return {"drugs": [dict(row) for row in rows]}
    finally:
        conn.close()


@app.get("/claims")
def list_claims(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM claims LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        return {"claims": [dict(row) for row in rows]}
    finally:
        conn.close()


@app.get("/claims/{claim_id}")
def get_claim(claim_id: int):
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM claims WHERE claimId = ?", (claim_id,)).fetchone()
        result = row_to_dict(row)
        if result is None:
            raise HTTPException(status_code=404, detail="Claim not found")
        return result
    finally:
        conn.close()


@app.post("/claims")
def create_claim(payload: Dict[str, Any]):
    data = Claim(**payload)
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO claims(patientId, providerId, drugNdc, amount, status, submittedAt) VALUES (?, ?, ?, ?, ?, ?)",
            (data.patientId, data.providerId, data.drugNdc, data.amount, data.status, data.submittedAt),
        )
        conn.commit()
        claim_id = cursor.lastrowid
        return {"message": "Claim created", "claimId": claim_id, "claim": data.dict()}
    finally:
        conn.close()


@app.put("/claims/{claim_id}")
def update_claim(claim_id: int, payload: Dict[str, Any]):
    allowed_columns = ["patientId", "providerId", "drugNdc", "amount", "status", "submittedAt"]
    update_clause, values = build_update_clause(payload, allowed_columns)
    if not update_clause:
        raise HTTPException(status_code=400, detail="No updatable claim fields provided")
    conn = get_db_connection()
    try:
        cursor = conn.execute(f"UPDATE claims SET {update_clause} WHERE claimId = ?", (*values, claim_id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Claim not found")
        return {"message": "Claim updated"}
    finally:
        conn.close()


@app.delete("/claims/{claim_id}")
def delete_claim(claim_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.execute("DELETE FROM claims WHERE claimId = ?", (claim_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Claim not found")
        return {"message": "Claim deleted"}
    finally:
        conn.close()


@app.get("/claims/status/{status}")
def claims_by_status(status: str):
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM claims WHERE status = ?", (status,)).fetchall()
        return {"claims": [dict(row) for row in rows]}
    finally:
        conn.close()


from mcp import router as mcp_router

app.include_router(ebv_router)
app.include_router(mcp_router)
