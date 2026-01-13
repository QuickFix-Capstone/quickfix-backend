#!/usr/bin/env bash
set -e

FUNC_NAME="get_job_reviews"
SRC_DIR="../lambda/reviews/get_job_reviews"
BUILD_DIR=".build/${FUNC_NAME}"
ZIP_FILE="${FUNC_NAME}.zip"
AWS_REGION="us-east-2"
AWS_PROFILE="QuickFix NoSql DB"
REQ_FILE="../lambda_requirements.txt"


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
  --region "$AWS_REGION" \
  --profile "$AWS_PROFILE"


echo "✅ Deployed ${FUNC_NAME}"
