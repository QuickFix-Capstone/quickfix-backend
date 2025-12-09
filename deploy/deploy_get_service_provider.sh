#!/usr/bin/env bash
set -e

FUNC_NAME="get_service_provider"
SRC_DIR="../lambda/service_providers/get_service_provider"
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
pip install -r "${REQ_FILE}" -t "$BUILD_DIR" > /dev/null

echo "👉 Creating zip..."
cd "$BUILD_DIR"
zip -r "../${ZIP_FILE}" . > /dev/null
cd - > /dev/null

echo "👉 Updating Lambda code: ${FUNC_NAME} ..."
aws lambda update-function-code \
  --region "$AWS_REGION" \
  --function-name "$FUNC_NAME" \
  --zip-file "fileb://.build/${ZIP_FILE}"

echo "✅ Done."