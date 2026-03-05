QuickFix Admin Refunds - Get Request Details Lambda
===================================================

Handler: lambda_function.lambda_handler
Route:   GET /admin/refunds/{refund_request_id}
Auth:    Attach QuickFixAdminJwtAuthorizer (JWT)

Required environment variables:
  MYSQL_HOST
  MYSQL_USER
  MYSQL_PASSWORD
  MYSQL_DB
  MYSQL_PORT (default 3306)

  REFUND_BUCKET = quickfix-app-files
  REFUND_VIEW_TTL_SECONDS = 900

IAM permissions needed on this Lambda's execution role:
  s3:GetObject on arn:aws:s3:::quickfix-app-files/refunds/*

Notes:
  - Returns refund_request plus attachments with presigned GET view_url links.
