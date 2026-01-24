#!/usr/bin/env bash
set -e

FUNC_NAME="create_customer"
SRC_DIR="../lambda/customers/create_customer"
BUILD_DIR=".build/${FUNC_NAME}"
ZIP_FILE="${FUNC_NAME}.zip"
AWS_REGION="us-east-2"
REQ_FILE="../lambda_requirements.txt"   # 👈 shared requirements

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
  --function-name "$FUNC_NAME" \
  --zip-file "fileb://.build/${ZIP_FILE}" \
  --region "$AWS_REGION"

echo "👉 Updating Lambda environment variables..."
aws lambda update-function-configuration \
  --function-name "$FUNC_NAME" \
  --environment "Variables={COGNITO_USER_POOL_ID=us-east-2_45z5OMePi,AWS_REGION=${AWS_REGION}}" \
  --region "$AWS_REGION"

echo "✅ Deployed ${FUNC_NAME}"