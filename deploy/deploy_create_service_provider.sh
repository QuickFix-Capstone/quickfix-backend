#!/usr/bin/env bash
set -e

FUNC_NAME="create_service_provider"                      # 👈 Lambda function name in AWS
SRC_DIR="../lambda/service_providers/create_service_provider"    # 👈 adjust if your path is different
BUILD_DIR=".build/${FUNC_NAME}"
ZIP_FILE="${FUNC_NAME}.zip"
AWS_REGION="us-east-2"                                   # 👈 same region as your other Lambdas
REQ_FILE="../lambda_requirements.txt"                    # 👈 shared requirements

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

echo "👉 Updating Lambda code: ${FUNC_NAME} ..."
aws lambda update-function-code \
  --region "$AWS_REGION" \
  --function-name "$FUNC_NAME" \
  --zip-file "fileb://.build/${ZIP_FILE}"

echo "✅ Done. Deployed ${FUNC_NAME}."