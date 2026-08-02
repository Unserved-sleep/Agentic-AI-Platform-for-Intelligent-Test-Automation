# Business Requirements Document (BRD): Auto Insurance Claims Portal

## 1. Objective
The objective of this project is to launch a new web-based Claims Portal for our Auto Insurance customers. This portal will allow policyholders to submit claims digitally, and enable claims adjusters to review, approve, or reject claims efficiently.

## 2. Actors & Roles
*   **Claimant (Policyholder):** Can submit new claims, upload evidence (photos/documents), and view the status of their own claims.
*   **Claims Adjuster:** Can view all submitted claims, request additional information, approve, or reject claims.
*   **Read-Only Auditor:** Can view claims and histories but cannot change status or approve payouts.
*   **System:** Automatically validates policies, calculates initial estimates, and auto-approves low-risk claims.

## 3. Claim Lifecycle & Status Workflow
A claim must strictly follow these status transitions:
1.  `DRAFT`: Claim initiated but not yet submitted.
2.  `SUBMITTED`: Claim submitted by the Claimant.
3.  `UNDER_REVIEW`: Claim picked up by a Claims Adjuster.
4.  `APPROVED` or `REJECTED`: Final decision made by Adjuster or System.
5.  `PAID`: If approved, the payout is processed and recorded.

## 6. Business Rules
*   **BR-01 (Auto-Approval):** Claims with an estimated payout of less than $500.00 MUST be automatically transitioned to `APPROVED` if the policyholder has zero claims in the past 12 months.
*   **BR-02 (Required Documentation):** Any claim with an estimated payout >= $500.00 requires at least one (1) image attachment before it can transition from `SUBMITTED` to `UNDER_REVIEW`.
*   **BR-03 (Role Authorization):** Only a user with the `Claims Adjuster` role can trigger the `approve` action. If a `Read-Only Auditor` or `Claimant` attempts to approve, the system must return a 403 Forbidden error.
*   **BR-04 (Data Persistence):** Upon transitioning to `APPROVED`, a corresponding payout record MUST be created in the database.

## 7. API Reference (Backend Scope)
*   `POST /api/v1/claims`: Create a new claim.
    *   Payload requires: `policy_number`, `incident_date`, `description`, `claim_amount`.
*   `GET /api/v1/claims/{claim_id}`: Retrieve claim details.
*   `POST /api/v1/claims/{claim_id}/approve`: Approve a claim.
    *   Requires Adjuster authorization.
    *   Moves status to `APPROVED` and generates payout.
