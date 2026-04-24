# MCP SQLite API Server with EBV Mock Integration

This project implements a comprehensive FastAPI-based MCP (Model Context Protocol) server with SQLite database operations and EBV (Electronic Benefits Verification) mock API integration. The system provides 30+ database CRUD/search endpoints, MCP routing for intent-driven requests, and a mock EBV benefits check API with scenario-based responses.

## System Overview

The application consists of three main components:

1. **Database Layer** (`main.py`): FastAPI app with SQLite-backed CRUD operations for healthcare entities (patients, providers, payers, drugs, claims).
2. **MCP Routing Layer** (`mcp.py`): Intent-driven routing that validates payloads before executing operations.
3. **EBV Mock API** (`ebv.py`): Simulated benefits verification endpoint with configurable scenarios.

### Architecture Flow

```
Client Request → MCP Router → Validation → Operation Execution → Response
                                      ↓
                               EBV Benefits Check (if applicable)
```

- **MCP Layer**: Acts as a gatekeeper. Validates required fields before routing to database operations or EBV API.
- **Database Operations**: Direct CRUD/search on SQLite tables.
- **EBV Integration**: Mock benefits checks with scenario-based responses, requiring proper authorization and payload validation.

## Features

- **30 Database APIs**: Full CRUD + search for 5 entity types (patients, providers, payers, drugs, claims).
- **MCP Intent Routing**: `POST /mcp/request` routes based on intent strings.
- **EBV Mock Scenarios**: 8 configurable response scenarios for benefits checks.
- **Input Validation**: Prevents API calls with missing required fields.
- **SQLite Backend**: Lightweight, file-based database with sample data.
- **FastAPI Framework**: Async-capable, auto-generated OpenAPI docs.

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Clone/Navigate to Project Directory**:
   ```bash
   cd /workspaces/dataoutput
   ```

2. **Create Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database**:
   ```bash
   python init_db.py
   ```
   This creates `data.db` with sample data for all tables.

5. **Start the Server**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Verify Installation**:
   - Open http://localhost:8000/docs for FastAPI interactive docs.
   - Check http://localhost:8000/mcp/routes for available MCP operations.

## API Endpoints

### Database APIs (Direct Access)

#### Patients
- `GET /patients` - List patients (pagination: limit, offset)
- `GET /patients/{patient_id}` - Get specific patient
- `POST /patients` - Create patient
- `PUT /patients/{patient_id}` - Update patient
- `DELETE /patients/{patient_id}` - Delete patient
- `GET /patients/search` - Search by name or payerId

#### Providers
- `GET /providers` - List providers
- `GET /providers/{provider_id}` - Get provider
- `POST /providers` - Create provider
- `PUT /providers/{provider_id}` - Update provider
- `DELETE /providers/{provider_id}` - Delete provider
- `GET /providers/search` - Search by name or specialty

#### Payers
- `GET /payers` - List payers
- `GET /payers/{payer_id}` - Get payer
- `POST /payers` - Create payer
- `PUT /payers/{payer_id}` - Update payer
- `DELETE /payers/{payer_id}` - Delete payer
- `GET /payers/active` - List active payers only

#### Drugs
- `GET /drugs` - List drugs
- `GET /drugs/{drug_ndc}` - Get drug
- `POST /drugs` - Create drug
- `PUT /drugs/{drug_ndc}` - Update drug
- `DELETE /drugs/{drug_ndc}` - Delete drug
- `GET /drugs/search` - Search by name or strength

#### Claims
- `GET /claims` - List claims
- `GET /claims/{claim_id}` - Get claim
- `POST /claims` - Create claim
- `PUT /claims/{claim_id}` - Update claim
- `DELETE /claims/{claim_id}` - Delete claim
- `GET /claims/status/{status}` - Filter claims by status

### MCP Routing Layer

- `POST /mcp/request` - Intent-driven routing with validation
- `POST /mcp/route/{operation}` - Direct operation routing
- `GET /mcp/routes` - List available operations

### EBV Mock API

- `POST /ebv/benefits` - Benefits verification with scenario control

## How the Process Works

### 1. Request Flow

1. **Client sends request** to `POST /mcp/request` with `intent` and `payload`.
2. **MCP Router** (`mcp.py`):
   - Maps intent to operation (e.g., "benefits_check" → "benefits_check").
   - Validates required payload fields.
   - If validation fails, returns error with missing fields.
   - If validation passes, executes the operation.
3. **Operation Execution**:
   - For database ops: Calls corresponding function in `main.py`.
   - For EBV: Calls `process_ebv_benefits` in `ebv.py`.
4. **Response**: Returns success/error with result data.

### 2. EBV Benefits Check Process

1. **MCP Validation**: Ensures `npi`, `patientId`, `patientDob`, `drugNdc` are present.
2. **EBV Processing** (`ebv.py`):
   - Checks `Authorization` header.
   - Uses `x-scenario` header to select response.
   - Returns scenario-specific mock data.
3. **Error Handling**: Returns 401 for missing auth, 400 for missing fields, 504 for timeout simulation.

### 3. Database Operations

- All operations use SQLite with row factory for dict results.
- Updates use dynamic SQL clause building.
- Integrity errors handled for duplicate keys.
- Pagination supported on list endpoints.

## Testing Procedures

### Manual Testing with cURL

#### 1. Start Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Test MCP Routes List
```bash
curl http://localhost:8000/mcp/routes
```
Expected: JSON array of 31 operations including "benefits_check".

#### 3. Test Database Operation via MCP
```bash
curl -X POST http://localhost:8000/mcp/request \
  -H 'Content-Type: application/json' \
  -d '{
    "intent": "list_patients",
    "payload": {"limit": 2}
  }'
```
Expected: Success with patient list.

#### 4. Test Validation Error
```bash
curl -X POST http://localhost:8000/mcp/request \
  -H 'Content-Type: application/json' \
  -d '{
    "intent": "get_patient",
    "payload": {}
  }'
```
Expected: 400 error with missing "patientId".

#### 5. Test EBV Benefits Check
```bash
curl -X POST http://localhost:8000/mcp/request \
  -H 'Content-Type: application/json' \
  -d '{
    "intent": "benefits_check",
    "payload": {
      "npi": "1234567890",
      "patientId": "P001",
      "patientDob": "1980-01-01",
      "drugNdc": "12345-001",
      "scenario": "covered_pa_required",
      "authorization": "Bearer test-token"
    }
  }'
```
Expected: Success with benefits response.

#### 6. Test EBV Direct Endpoint
```bash
curl -X POST http://localhost:8000/ebv/benefits \
  -H 'Content-Type: application/json' \
  -H 'x-scenario: covered_no_restrictions' \
  -H 'Authorization: Bearer test-token' \
  -d '{
    "payload": {
      "npi": "1234567890",
      "patientId": "P001",
      "patientDob": "1980-01-01",
      "drugNdc": "12345-001"
    }
  }'
```
Expected: Scenario-specific response.

#### 7. Test Database CRUD
```bash
# Create patient
curl -X POST http://localhost:8000/patients \
  -H 'Content-Type: application/json' \
  -d '{
    "patientId": "TEST001",
    "name": "Test Patient",
    "dob": "1990-01-01",
    "gender": "other",
    "payerId": "PAY001"
  }'

# Get patient
curl http://localhost:8000/patients/TEST001

# Update patient
curl -X PUT http://localhost:8000/patients/TEST001 \
  -H 'Content-Type: application/json' \
  -d '{"name": "Updated Test Patient"}'

# Delete patient
curl -X DELETE http://localhost:8000/patients/TEST001
```

### Automated Testing with pytest

1. **Install pytest**:
   ```bash
   pip install pytest httpx
   ```

2. **Create test file** (`test_api.py`):
   ```python
   import pytest
   from fastapi.testclient import TestClient
   from main import app

   client = TestClient(app)

   def test_mcp_routes():
       response = client.get("/mcp/routes")
       assert response.status_code == 200
       assert "benefits_check" in response.json()["available_routes"]

   def test_patient_crud():
       # Create
       response = client.post("/patients", json={
           "patientId": "TEST001",
           "name": "Test Patient",
           "dob": "1990-01-01",
           "gender": "other",
           "payerId": "PAY001"
       })
       assert response.status_code == 200

       # Read
       response = client.get("/patients/TEST001")
       assert response.status_code == 200
       assert response.json()["name"] == "Test Patient"

       # Update
       response = client.put("/patients/TEST001", json={"name": "Updated"})
       assert response.status_code == 200

       # Delete
       response = client.delete("/patients/TEST001")
       assert response.status_code == 200

   def test_mcp_validation():
       response = client.post("/mcp/request", json={
           "intent": "get_patient",
           "payload": {}
       })
       assert response.status_code == 400
       assert "missingFields" in response.json()

   def test_ebv_benefits():
       response = client.post("/mcp/request", json={
           "intent": "benefits_check",
           "payload": {
               "npi": "1234567890",
               "patientId": "P001",
               "patientDob": "1980-01-01",
               "drugNdc": "12345-001",
               "scenario": "covered_pa_required",
               "authorization": "Bearer test"
           }
       })
       assert response.status_code == 200
       assert response.json()["result"]["requiresPriorAuth"] == True
   ```

3. **Run Tests**:
   ```bash
   pytest test_api.py -v
   ```

### Integration Testing

1. **Full Workflow Test**:
   - Create patient via MCP.
   - Create claim referencing that patient.
   - Run benefits check for the patient/drug.
   - Verify all operations succeed and data consistency.

2. **Load Testing**:
   - Use tools like `locust` or `ab` to simulate concurrent requests.
   - Test database performance under load.

3. **Error Scenarios**:
   - Test all EBV scenarios via MCP.
   - Verify timeout handling.
   - Test invalid intents and payloads.

## Error Handling

- **Validation Errors**: 400 with `missingFields` array.
- **Not Found**: 404 for missing resources.
- **Unauthorized**: 401 for missing EBV auth.
- **Integrity Errors**: 400 for duplicate keys.
- **Timeout Simulation**: 504 for `payer_timeout` scenario.

## Deployment

- **Production**: Use `uvicorn main:app --host 0.0.0.0 --port 8000` without `--reload`.
- **Database**: SQLite is file-based; ensure write permissions.
- **Environment Variables**: Add secrets for real EBV integration.
- **Scaling**: For high load, consider PostgreSQL instead of SQLite.

## Troubleshooting

- **Import Errors**: Ensure all files are in the same directory.
- **Database Issues**: Delete `data.db` and re-run `init_db.py`.
- **Port Conflicts**: Change port in uvicorn command.
- **Validation Fails**: Check payload structure against API docs.

## Contributing

- Add new operations to `VALID_ACTIONS` and `execute_operation`.
- Update `INTENT_ROUTE_MAP` for new intents.
- Add tests for new features.

This documentation covers the complete system workflow, setup, testing, and maintenance procedures.
