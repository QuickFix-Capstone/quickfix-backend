#!/usr/bin/env bash
set -e

FUNC_NAME="get_admin_analytics_v1"
SRC_DIR="../lambda/admin/get_admin_analytics_v1"
BUILD_DIR=".build/${FUNC_NAME}"
ZIP_FILE="${FUNC_NAME}.zip"
AWS_REGION="us-east-2"
REQ_FILE="../lambda_requirements.txt"

echo "Cleaning build dir..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "Copying source code..."
cp "${SRC_DIR}/handler.py" "$BUILD_DIR/"
cp -r ../src "$BUILD_DIR/"

echo "Installing dependencies from ${REQ_FILE}..."
pip install -r "${REQ_FILE}" -t "$BUILD_DIR" > /dev/null

echo "Creating zip..."
cd "$BUILD_DIR"
zip -r "../${ZIP_FILE}" . > /dev/null
cd - > /dev/null

echo "Updating Lambda code: ${FUNC_NAME}..."
aws lambda update-function-code \
  --function-name "$FUNC_NAME" \
  --zip-file "fileb://.build/${ZIP_FILE}" \
  --region "$AWS_REGION" \
  --no-cli-pager > /dev/null

echo "Deployed ${FUNC_NAME}"
