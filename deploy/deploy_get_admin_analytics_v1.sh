#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

FUNC_NAME="get_admin_analytics_v1"
SRC_DIR="${REPO_ROOT}/lambda/admin/get_admin_analytics_v1"
BUILD_DIR="${REPO_ROOT}/.build/${FUNC_NAME}"
ZIP_FILE="${FUNC_NAME}.zip"
AWS_REGION="us-east-2"
REQ_FILE="${REPO_ROOT}/lambda_requirements.txt"

echo "Cleaning build dir..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "Copying source code..."
cp "${SRC_DIR}/handler.py" "$BUILD_DIR/"
cp -r "${REPO_ROOT}/src" "$BUILD_DIR/"

echo "Installing dependencies from ${REQ_FILE}..."
pip install -r "${REQ_FILE}" -t "$BUILD_DIR" > /dev/null

echo "Creating zip..."
cd "$BUILD_DIR"
zip -r "../${ZIP_FILE}" . > /dev/null
cd - > /dev/null

echo "Updating Lambda code: ${FUNC_NAME}..."
aws lambda update-function-code \
  --function-name "$FUNC_NAME" \
  --zip-file "fileb://${REPO_ROOT}/.build/${ZIP_FILE}" \
  --region "$AWS_REGION" \
  --no-cli-pager > /dev/null

echo "Deployed ${FUNC_NAME}"
