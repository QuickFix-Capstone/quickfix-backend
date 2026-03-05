Refund Presign Uploads Lambda
- Route: POST /refunds/presign-uploads
- Env:
  REFUND_BUCKET=quickfix-app-files
  REFUND_UPLOAD_TTL_SECONDS=900
  REFUND_MAX_FILES=5
  MYSQL_HOST=...
  MYSQL_USER=...
  MYSQL_PASSWORD=...
  MYSQL_DB=...
  MYSQL_PORT=3306
- IAM (role):
  s3:PutObject on arn:aws:s3:::quickfix-app-files/refunds/*
  (optional) s3:GetObject for later admin viewing
