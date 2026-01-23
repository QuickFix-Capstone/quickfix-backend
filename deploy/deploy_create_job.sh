#!/bin/bash

# Deploy create_job Lambda function
# This script packages and deploys the create_job function to AWS Lambda

set -e

FUNCTION_NAME="create_job"
BUILD_DIR=".build"
LAMBDA_DIR="../lambda/jobs/create_job"

echo "👉 Cleaning build dir..."
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

echo "👉 Copying source code..."
cp $LAMBDA_DIR/handler.py $BUILD_DIR/

echo "👉 Copying shared modules..."
cp -r ../src $BUILD_DIR/

echo "👉 Installing dependencies from ../lambda_requirements.txt ..."
pip install -r ../lambda_requirements.txt -t $BUILD_DIR/ --quiet

echo "👉 Creating zip..."
cd $BUILD_DIR
zip -r create_job.zip . -q
cd ..

echo "👉 Updating Lambda code: $FUNCTION_NAME ..."
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://$BUILD_DIR/create_job.zip \
    --region us-east-2

echo "✅ Deployment complete!"
