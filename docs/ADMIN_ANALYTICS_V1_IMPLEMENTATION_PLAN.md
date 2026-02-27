# Admin Analytics V1 - Implementation Plan

## Goal
Deliver an Admin Analytics V1 API that is restricted to Cognito administrators only.

## Auth Contract
- JWT claim key: `cognito:groups`
- Required group: `Administrator`
- Temporary compatibility: allow `Adminstrator` if that typo already exists in Cognito

## Phase 1 (Now): Auth Guard Foundation
1. Add shared claim extraction and group-check helpers.
2. Standardize admin check using:
   - `extract_jwt_claims(event)`
   - `is_cognito_administrator(claims)`
3. Return `403` for authenticated non-admin users.
4. Return `401` for missing/invalid JWT claims.

## Phase 2: Admin Analytics V1 Endpoint
1. Create Lambda: `lambda/admin/get_admin_analytics_v1/handler.py`
2. Endpoint proposal: `GET /admin/analytics/v1`
3. Apply guard first:
   - Parse claims
   - Check admin group
   - Stop request if unauthorized
4. Return initial KPI set (read-only):
   - `customers_total`
   - `providers_total`
   - `jobs_total`
   - `bookings_total`
   - `reviews_total`

## Phase 3: Deployment
1. Add API Gateway route for `GET /admin/analytics/v1`.
2. Attach existing Cognito JWT authorizer.
3. Deploy Lambda + route permissions.
4. Validate with:
   - admin token -> `200`
   - non-admin token -> `403`
   - missing token -> `401`

## Phase 4: Hardening
1. Add structured logs with request id and admin subject (`sub`).
2. Add CloudWatch metric for unauthorized admin attempts.
3. Remove typo fallback (`Adminstrator`) after Cognito groups are normalized.

## Current Status
- Shared auth helpers are implemented in `src/utils/auth.py`.
- Unit tests added in `tests/test_auth_utils.py`.
