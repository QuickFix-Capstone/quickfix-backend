#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <lambda_dir> <function_name>"
  exit 1
fi

LAMBDA_DIR="$1"
FUNCTION_NAME="$2"
BUILD_DIR="deploy/.build/${FUNCTION_NAME}"

if [ ! -f "${LAMBDA_DIR}/handler.py" ]; then
  echo "❌ Missing handler: ${LAMBDA_DIR}/handler.py"
  exit 1
fi

echo "📦 Building ${FUNCTION_NAME} Lambda package..."
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

cp "${LAMBDA_DIR}/handler.py" "${BUILD_DIR}/"

if [ -d src ]; then
  cp -r src "${BUILD_DIR}/"
fi

if [ -f "${LAMBDA_DIR}/requirements.txt" ]; then
  pip install -r "${LAMBDA_DIR}/requirements.txt" -t "${BUILD_DIR}/" --quiet
fi

(
  cd "${BUILD_DIR}"
  zip -r "../${FUNCTION_NAME}.zip" . -q
)

echo "📤 Deploying ${FUNCTION_NAME} to AWS Lambda..."
aws lambda update-function-code \
  --function-name "${FUNCTION_NAME}" \
  --zip-file "fileb://deploy/.build/${FUNCTION_NAME}.zip" \
  --no-cli-pager >/dev/null

echo "✅ ${FUNCTION_NAME} deployed successfully"
