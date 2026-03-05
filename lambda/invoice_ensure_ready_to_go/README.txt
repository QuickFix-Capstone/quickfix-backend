Invoice Ensure Lambda (API Gateway)

POST /payments/{paymentId}/invoice/ensure

- If invoices/{paymentId}/invoice.pdf exists in S3 -> returns presigned URL
- Else -> sends SQS message {"payment_id": <id>, "reason":"receipt_page"} and returns 202 queued

Env vars (Lambda):
  INVOICE_BUCKET=quickfix-invoices-dev
  INVOICE_JOBS_QUEUE_URL=https://sqs.us-east-2.amazonaws.com/<acct>/invoice-jobs-dev
  INVOICE_URL_TTL_SECONDS=900   (optional)
  CORS_ALLOW_ORIGIN=http://localhost:5173  (optional, default *)

IAM permissions (Lambda role) minimum:
  s3:HeadObject on arn:aws:s3:::quickfix-invoices-dev/*
  s3:GetObject  on arn:aws:s3:::quickfix-invoices-dev/*  (for presign target)
  sqs:SendMessage on arn:aws:sqs:us-east-2:<acct>:invoice-jobs-dev
