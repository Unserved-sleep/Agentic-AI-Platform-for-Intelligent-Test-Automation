# Business Requirements Document (BRD) & API Spec
## Project: Insurance Claims Management Portal

### 1. Business Overview
The Claims Management Portal is an enterprise service for policyholders and claims adjusters to process, approve, and disburse vehicle and property insurance claims.

### 2. User Roles & Actors
- **Policyholder**: Submits claims, views claim status.
- **Claims Adjuster**: Reviews submitted claims, approves or rejects claims.
- **Finance Manager**: Oversees payout disbursement.

### 3. Business Workflows & Validations
- **BRD-WF-1: Submit Claim**
  - Input fields: `policy_number`, `claimant_name`, `claim_amount`, `incident_date`, `description`.
  - Validation 1: `claim_amount` must be greater than 0 and less than $50,000.
  - Validation 2: Initial status must automatically be set to `SUBMITTED`.

- **BRD-WF-2: Approve Claim**
  - An adjuster submits POST request to `/api/v1/claims/{id}/approve`.
  - Validation 1: Claim status must transition from `SUBMITTED` or `IN_REVIEW` to `APPROVED`.
  - Validation 2 (Backend DB Rule): Upon approval, the system must automatically create a record in the `payouts` database table with `payout_amount` equal to `claim_amount` and `status` set to `PROCESSED`.

- **BRD-WF-3: Reject Claim**
  - An adjuster submits POST request to `/api/v1/claims/{id}/reject`.
  - Validation 1: Claim status must transition to `REJECTED`. No payout record should be created.

### 4. API Endpoints Specification
- `GET /api/v1/claims`: List all claims.
- `GET /api/v1/claims/{id}`: Get claim by ID.
- `POST /api/v1/claims`: Submit new claim. Payload: `{"policy_number": string, "claimant_name": string, "claim_amount": number, "incident_date": string, "description": string}`.
- `POST /api/v1/claims/{id}/approve`: Approve claim and initiate payout.
- `POST /api/v1/claims/{id}/reject`: Reject claim.
- `GET /api/v1/payouts`: List all payout records.
