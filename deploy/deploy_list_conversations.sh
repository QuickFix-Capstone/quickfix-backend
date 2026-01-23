#!/bin/bash
set -e

FUNCTION_NAME="list_conversations"
LAMBDA_DIR="lambda/messages/list_conversations"
BUILD_DIR="deploy/.build/${FUNCTION_NAME}"

echo "📦 Building ${FUNCTION_NAME} Lambda package..."
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

# Copy handler
cp $LAMBDA_DIR/handler.py $BUILD_DIR/

# Copy shared source code
cp -r src $BUILD_DIR/

# Install dependencies
if [ -f "${LAMBDA_DIR}/requirements.txt" ]; then
    pip install -r "${LAMBDA_DIR}/requirements.txt" -t "${BUILD_DIR}/" --quiet
fi

# Create zip
cd $BUILD_DIR
zip -r ../${FUNCTION_NAME}.zip . -q
cd ../../..

echo "📤 Deploying to AWS Lambda..."
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://deploy/.build/${FUNCTION_NAME}.zip \
    --no-cli-pager

echo "✅ ${FUNCTION_NAME} deployed successfully!"
