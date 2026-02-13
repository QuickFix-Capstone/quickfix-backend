#!/bin/bash
set -e

FUNCTION_NAME="customer_update_job_application"
LAMBDA_DIR="lambda/jobs/customer_update_job_application"
BUILD_DIR="deploy/.build/${FUNCTION_NAME}"

echo "Building ${FUNCTION_NAME} Lambda package..."

rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

cp "${LAMBDA_DIR}/handler.py" "${BUILD_DIR}/"
cp -r src "${BUILD_DIR}/"

if [ -f "${LAMBDA_DIR}/requirements.txt" ]; then
    pip install -r "${LAMBDA_DIR}/requirements.txt" -t "${BUILD_DIR}/" --quiet
fi

cd "${BUILD_DIR}"
zip -r "../${FUNCTION_NAME}.zip" . -q

echo "Deploying to AWS Lambda..."
aws lambda update-function-code \
    --function-name "${FUNCTION_NAME}" \
    --zip-file "fileb://../${FUNCTION_NAME}.zip" \
    --no-cli-pager

echo "${FUNCTION_NAME} deployed successfully!"
