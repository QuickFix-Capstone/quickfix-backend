QuickFix Admin Refunds - Review (Approve/Reject) Lambda
======================================================

Handler: lambda_function.lambda_handler
Route:   POST /admin/refunds/{refund_request_id}/review
Auth:    Attach QuickFixAdminJwtAuthorizer (JWT)

Request body JSON:
  { "action": "APPROVE" | "REJECT", "admin_note": "optional note" }

Required environment variables:
  MYSQL_HOST
  MYSQL_USER
  MYSQL_PASSWORD
  MYSQL_DB
  MYSQL_PORT (default 3306)

Notes:
  - Only allows review when current status is PENDING.
  - Sets status to APPROVED or REJECTED and sets reviewed_at=NOW().
