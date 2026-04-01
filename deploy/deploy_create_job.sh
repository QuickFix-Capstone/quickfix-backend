#!/bin/bash

# Deploy create_job Lambda function
# This script packages and deploys the create_job function to AWS Lambda

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FUNCTION_NAME="create_job"
BUILD_DIR="$SCRIPT_DIR/.build"
LAMBDA_DIR="$REPO_ROOT/lambda/jobs/create_job"

echo "👉 Cleaning build dir..."
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

echo "👉 Copying source code..."
cp $LAMBDA_DIR/handler.py $BUILD_DIR/

echo "👉 Copying shared modules..."
cp -r "$REPO_ROOT/src" "$BUILD_DIR/"

echo "👉 Installing dependencies from $REPO_ROOT/lambda_requirements.txt ..."
pip install -r "$REPO_ROOT/lambda_requirements.txt" -t "$BUILD_DIR/" --quiet

echo "👉 Creating zip..."
cd "$BUILD_DIR"
zip -r create_job.zip . -q
cd "$SCRIPT_DIR"

echo "👉 Updating Lambda code: $FUNCTION_NAME ..."
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://$BUILD_DIR/create_job.zip \
    --region us-east-2

echo "👉 Ensuring API Gateway route exists: POST /jobs ..."
bash "$SCRIPT_DIR/setup_create_job_route.sh"

echo "✅ Deployment complete!"
