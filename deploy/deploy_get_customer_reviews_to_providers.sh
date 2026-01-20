#!/usr/bin/env bash
set -e

FUNC_NAME="get_customer_reviews_to_providers"
SRC_DIR="../lambda/reviews/get_customer_reviews_to_providers"
BUILD_DIR=".build/${FUNC_NAME}"
ZIP_FILE="${FUNC_NAME}.zip"
AWS_REGION="us-east-2"
REQ_FILE="../lambda_requirements.txt"

echo "👉 Cleaning build dir..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "👉 Copying source code..."
cp "${SRC_DIR}/handler.py" "$BUILD_DIR/"
cp -r ../src "$BUILD_DIR/"

echo "👉 Installing dependencies..."
pip install -r "${REQ_FILE}" -t "$BUILD_DIR" > /dev/null 2>&1

echo "👉 Creating zip..."
cd "$BUILD_DIR"
zip -r "../${ZIP_FILE}" . > /dev/null
cd - > /dev/null

echo "👉 Updating Lambda code..."
aws lambda update-function-code \
  --function-name "$FUNC_NAME" \
  --zip-file "fileb://.build/${ZIP_FILE}" \
  --region "$AWS_REGION"

echo "✅ Deployed ${FUNC_NAME}"
