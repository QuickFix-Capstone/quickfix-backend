#!/usr/bin/env bash
# Create the get_booking_details Lambda function in AWS

set -e

FUNC_NAME="get_booking_details"
# Using an existing role similar to other booking lambdas if possible, or create new. 
# Re-using get_customer_bookings role or similar might be easiest if we don't have a dedicated one yet.
# But usually we create a new role or use a shared one. Let's reuse the one from get_customer_reviews for now or try to find a better one.
# Actually, the user's previous output showed `get_customer_bookings-role-17ll6i6r`.
ROLE_ARN="arn:aws:iam::008971679867:role/service-role/get_customer_bookings-role-17ll6i6r" 
AWS_REGION="us-east-2"

# RDS Database credentials
MYSQL_HOST="quickfix-mysql.cno624c2aarh.us-east-2.rds.amazonaws.com"
MYSQL_USER="admin"
MYSQL_PASSWORD="QuickFix123!"
MYSQL_DB="quickfix"
MYSQL_PORT="3306"

echo "🚀 Creating Lambda function: ${FUNC_NAME}..."

# Create a minimal zip file for initial creation
TEMP_DIR=$(mktemp -d)
echo "import json; def handler(event, context): return {'statusCode': 200}" > "${TEMP_DIR}/handler.py"
cd "${TEMP_DIR}"
zip function.zip handler.py > /dev/null
cd - > /dev/null

# Create the Lambda function
aws lambda create-function \
  --function-name "${FUNC_NAME}" \
  --runtime python3.11 \
  --role "${ROLE_ARN}" \
  --handler handler.handler \
  --zip-file "fileb://${TEMP_DIR}/function.zip" \
  --region "${AWS_REGION}" \
  --timeout 30 \
  --memory-size 256 \
  --environment "Variables={MYSQL_HOST=${MYSQL_HOST},MYSQL_USER=${MYSQL_USER},MYSQL_PASSWORD=${MYSQL_PASSWORD},MYSQL_DB=${MYSQL_DB},MYSQL_PORT=${MYSQL_PORT}}" \
  --description "Get detailed booking information including images"

# Clean up temp files
rm -rf "${TEMP_DIR}"

echo ""
echo "✅ Lambda function created successfully!"
echo ""
echo "Now deploying the actual code..."
./deploy/deploy_get_booking_details.sh
