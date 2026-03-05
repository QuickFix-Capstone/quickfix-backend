QuickFix Admin Refunds - List Requests Lambda
============================================

Handler: lambda_function.lambda_handler
Route:   GET /admin/refunds?status=PENDING
Auth:    Attach QuickFixAdminJwtAuthorizer (JWT)

Required environment variables:
  MYSQL_HOST
  MYSQL_USER
  MYSQL_PASSWORD
  MYSQL_DB
  MYSQL_PORT (default 3306)

Notes:
  - Returns up to 200 refund requests ordered by requested_at DESC.
  - If status query param is provided, filters by that status.
