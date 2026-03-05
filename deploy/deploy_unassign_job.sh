#!/bin/bash
set -e

FUNCTION_NAME="unassign_job"
LAMBDA_DIR="lambda/ServiceProvider/unassign_job"
BUILD_DIR="deploy/.build/${FUNCTION_NAME}"

echo "📦 Building ${FUNCTION_NAME} Lambda package..."

# Clean and create build directory
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

# Copy handler
cp "${LAMBDA_DIR}/handler.py" "${BUILD_DIR}/"

# Copy shared source code
cp -r src "${BUILD_DIR}/"

# Install dependencies
if [ -f "${LAMBDA_DIR}/requirements.txt" ]; then
    pip install -r "${LAMBDA_DIR}/requirements.txt" -t "${BUILD_DIR}/" --quiet
fi

# Create deployment package
cd "${BUILD_DIR}"
zip -r "../${FUNCTION_NAME}.zip" . -q

echo "📤 Deploying to AWS Lambda..."
aws lambda update-function-code \
    --function-name "${FUNCTION_NAME}" \
    --zip-file "fileb://../${FUNCTION_NAME}.zip" \
    --no-cli-pager

echo "✅ ${FUNCTION_NAME} deployed successfully!"
