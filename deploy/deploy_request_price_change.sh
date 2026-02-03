#!/usr/bin/env bash
set -e

FUNC_NAME="request_price_change"
SRC_DIR="../lambda/jobs/request_price_change"
BUILD_DIR=".build/${FUNC_NAME}"
ZIP_FILE="${FUNC_NAME}.zip"
AWS_REGION="us-east-2"
REQ_FILE="${SRC_DIR}/requirements.txt"
IAM_ROLE="arn:aws:iam::008971679867:role/service-role/create_customer-role-qch33m23"

echo "🚀 Deploying ${FUNC_NAME} Lambda function..."
echo "============================================"

echo "👉 Cleaning build dir..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "👉 Copying source code..."
cp "${SRC_DIR}/handler.py" "$BUILD_DIR/"
cp -r ../src "$BUILD_DIR/"

# Check if requirements.txt exists, if not create a minimal one
if [ ! -f "$REQ_FILE" ]; then
    echo "👉 Creating requirements.txt..."
    echo "pymysql" > "$REQ_FILE"
fi

echo "👉 Installing dependencies from ${REQ_FILE}..."
pip install -r "${REQ_FILE}" -t "$BUILD_DIR" > /dev/null

echo "👉 Creating deployment package..."
cd "$BUILD_DIR"
zip -r "../${ZIP_FILE}" . > /dev/null
cd - > /dev/null

# Check if Lambda function exists
echo "👉 Checking if Lambda function exists..."
if aws lambda get-function --function-name "$FUNC_NAME" --region "$AWS_REGION" > /dev/null 2>&1; then
    echo "👉 Lambda exists. Updating code..."
    aws lambda update-function-code \
      --function-name "$FUNC_NAME" \
      --zip-file "fileb://.build/${ZIP_FILE}" \
      --region "$AWS_REGION"

    echo "👉 Updating function configuration..."
    aws lambda update-function-configuration \
      --function-name "$FUNC_NAME" \
      --timeout 30 \
      --memory-size 256 \
      --region "$AWS_REGION" > /dev/null
else
    echo "👉 Lambda doesn't exist. Creating new function..."
    aws lambda create-function \
      --function-name "$FUNC_NAME" \
      --runtime python3.9 \
      --role "$IAM_ROLE" \
      --handler handler.handler \
      --zip-file "fileb://.build/${ZIP_FILE}" \
      --timeout 30 \
      --memory-size 256 \
      --region "$AWS_REGION" \
      --environment "Variables={MYSQL_HOST=quickfix-mysql.cno624c2aarh.us-east-2.rds.amazonaws.com,MYSQL_USER=admin,MYSQL_PASSWORD=QuickFix123!,MYSQL_DB=quickfix}"
fi

echo ""
echo "✅ Deployed ${FUNC_NAME} successfully!"
echo "============================================"
echo "📋 Next steps:"
echo "   1. Run setup_request_price_change_route.sh to configure API Gateway"
echo "   2. Configure authorization if needed"
echo ""
