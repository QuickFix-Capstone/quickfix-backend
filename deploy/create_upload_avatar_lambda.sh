#!/usr/bin/env bash
# Create the upload_avatar Lambda function in AWS

set -e

FUNC_NAME="upload_avatar"
ROLE_ARN="arn:aws:iam::008971679867:role/service-role/create_customer-role-qch33m23"
AWS_REGION="us-east-2"
S3_BUCKET="quickfix-app-files"

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
  --runtime python3.9 \
  --role "${ROLE_ARN}" \
  --handler handler.handler \
  --zip-file "fileb://${TEMP_DIR}/function.zip" \
  --region "${AWS_REGION}" \
  --timeout 30 \
  --memory-size 128 \
  --environment "Variables={S3_BUCKET=${S3_BUCKET}}" \
  --description "Generate presigned S3 URLs for customer avatar uploads"

# Clean up temp files
rm -rf "${TEMP_DIR}"

echo ""
echo "✅ Lambda function created successfully!"
echo ""
echo "Now deploying the actual code..."
./deploy_upload_avatar.sh
