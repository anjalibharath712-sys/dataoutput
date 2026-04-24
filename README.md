# MCP SQLite API Server

This project implements a FastAPI + SQLite backend with 30 database APIs across five resource domains and a separated MCP routing module in `mcp.py`.

## Features

- 30 CRUD/search endpoints for:
  - `patients`
  - `providers`
  - `payers`
  - `drugs`
  - `claims`
- MCP routing via `POST /mcp/request`
- Direct MCP operation calls via `POST /mcp/route/{operation}`
- Database initialization with SQLite
- Request validation before database operations

## API endpoints

### Patients
- `GET /patients`
- `GET /patients/{patient_id}`
- `POST /patients`
- `PUT /patients/{patient_id}`
- `DELETE /patients/{patient_id}`
- `GET /patients/search`

### Providers
- `GET /providers`
- `GET /providers/{provider_id}`
- `POST /providers`
- `PUT /providers/{provider_id}`
- `DELETE /providers/{provider_id}`
- `GET /providers/search`

### Payers
- `GET /payers`
- `GET /payers/{payer_id}`
- `POST /payers`
- `PUT /payers/{payer_id}`
- `DELETE /payers/{payer_id}`
- `GET /payers/active`

### Drugs
- `GET /drugs`
- `GET /drugs/{drug_ndc}`
- `POST /drugs`
- `PUT /drugs/{drug_ndc}`
- `DELETE /drugs/{drug_ndc}`
- `GET /drugs/search`

### Claims
- `GET /claims`
- `GET /claims/{claim_id}`
- `POST /claims`
- `PUT /claims/{claim_id}`
- `DELETE /claims/{claim_id}`
- `GET /claims/status/{status}`

### EBV Mock API
- `POST /ebv/benefits` — mock endpoint for EBV benefits checks
  - Header `x-scenario`: select mock behavior
  - Header `Authorization`: required bearer token
  - Body: JSON payload with required fields
  - Required payload fields: `npi`, `patientId`, `patientDob`, `drugNdc`

Available `x-scenario` values:
- `covered_no_restrictions`
- `empty_body`
- `covered_pa_required`
- `covered_step_therapy`
- `not_covered_alternative`
- `no_active_coverage`
- `coverage_gap`
- `payer_timeout`

### MCP layer
- `POST /mcp/request` — routes benefits and database operations through `mcp.py`
- `POST /mcp/route/{operation}` — direct MCP operation routing
- `GET /mcp/routes` — list supported MCP operations

## Setup

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Initialize the SQLite database:

```bash
python init_db.py
```

4. Start the server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Example MCP request

```bash
curl -X POST http://localhost:8000/mcp/request \
  -H 'Content-Type: application/json' \
  -d '{
    "intent": "create_patient",
    "payload": {
      "patientId": "P003",
      "name": "Clara West",
      "dob": "1990-02-18",
      "gender": "female",
      "payerId": "PAY001"
    }
  }'
```

## Example MCP EBV benefits request

```bash
curl -X POST http://localhost:8000/mcp/request \
  -H 'Content-Type: application/json' \
  -d '{
    "intent": "benefits_check",
    "payload": {
      "npi": "1234567890",
      "patientId": "P1234",
      "patientDob": "1980-01-01",
      "drugNdc": "12345-6789-01",
      "scenario": "covered_pa_required",
      "authorization": "Bearer token-value"
    }
  }'
```

## Notes

- Use the MCP layer when you want intent-driven routing instead of direct REST path calls.
- The SQLite database file is `data.db`.
- If you need more operations, add new intent mappings in `main.py` and a corresponding path handler.
