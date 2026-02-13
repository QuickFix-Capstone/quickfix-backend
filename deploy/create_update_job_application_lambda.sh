#!/usr/bin/env bash
set -e

FUNC_NAME="update_job_application"
ROLE_ARN="arn:aws:iam::008971679867:role/service-role/create_customer-role-qch33m23"
AWS_REGION="us-east-2"

# RDS Database credentials
MYSQL_HOST="quickfix-mysql.cno624c2aarh.us-east-2.rds.amazonaws.com"
MYSQL_USER="admin"
MYSQL_PASSWORD="QuickFix123!"
MYSQL_DB="quickfix"
MYSQL_PORT="3306"

echo "Creating Lambda function: ${FUNC_NAME}..."

# Create a minimal zip for initial function creation.
TEMP_DIR=$(mktemp -d)
cat > "${TEMP_DIR}/handler.py" <<'PY'
def handler(event, context):
    return {"statusCode": 200, "body": "{}"}
PY
(
  cd "${TEMP_DIR}"
  zip function.zip handler.py > /dev/null
)

aws lambda create-function \
  --function-name "${FUNC_NAME}" \
  --runtime python3.9 \
  --role "${ROLE_ARN}" \
  --handler handler.handler \
  --zip-file "fileb://${TEMP_DIR}/function.zip" \
  --region "${AWS_REGION}" \
  --timeout 30 \
  --memory-size 256 \
  --environment "Variables={MYSQL_HOST=${MYSQL_HOST},MYSQL_USER=${MYSQL_USER},MYSQL_PASSWORD=${MYSQL_PASSWORD},MYSQL_DB=${MYSQL_DB},MYSQL_PORT=${MYSQL_PORT}}" \
  --description "Provider updates own pending job application"

rm -rf "${TEMP_DIR}"

echo "Lambda created. Deploying application code..."
bash deploy/deploy_update_job_application.sh

