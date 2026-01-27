#!/usr/bin/env bash
set -e

FUNC_NAME="get_booking_images"
SRC_DIR="../lambda/bookings/get_booking_images"
BUILD_DIR=".build/${FUNC_NAME}"
ZIP_FILE="${FUNC_NAME}.zip"
AWS_REGION="us-east-2"
REQ_FILE="${SRC_DIR}/requirements.txt"
IAM_ROLE="arn:aws:iam::008971679867:role/service-role/create_customer-role-qch33m23"

echo "👉 Cleaning build dir..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "👉 Copying source code..."
cp "${SRC_DIR}/handler.py" "$BUILD_DIR/"
cp -r ../src "$BUILD_DIR/"

echo "👉 Installing dependencies from ${REQ_FILE} ..."
pip install -r "${REQ_FILE}" -t "$BUILD_DIR" > /dev/null

echo "👉 Creating zip..."
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
      --environment "Variables={S3_BUCKET=quickfix-app-files,MYSQL_HOST=quickfix-mysql.cno624c2aarh.us-east-2.rds.amazonaws.com,MYSQL_USER=admin,MYSQL_PASSWORD=QuickFix123!,MYSQL_DB=quickfix,PRESIGNED_URL_EXPIRATION=3600}"
fi

echo "✅ Deployed ${FUNC_NAME}"
