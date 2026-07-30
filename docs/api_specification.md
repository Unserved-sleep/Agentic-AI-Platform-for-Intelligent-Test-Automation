# API Specification (Draft)

## Endpoint: Create Claim
- **URL**: `/api/v1/claims`
- **Method**: `POST`
- **Description**: Creates a new insurance claim.

### Request Body
```json
{
  "policy_number": "string",
  "incident_date": "YYYY-MM-DD",
  "claim_type": "string (cashless|reimbursement)",
  "estimated_amount": "number"
}
```

### Response
```json
{
  "claim_id": "string",
  "status": "string (pending|approved|rejected)",
  "message": "string"
}
```

## Endpoint: Get Policy Details
- **URL**: `/api/v1/policies/{policy_id}`
- **Method**: `GET`
- **Description**: Retrieves policy details by ID.
