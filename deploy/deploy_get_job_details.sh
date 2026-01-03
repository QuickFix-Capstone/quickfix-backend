#!/bin/bash

# Deploy get_job_details Lambda function
# This script packages and deploys the get_job_details function to AWS Lambda

set -e

FUNCTION_NAME="get_job_details"
BUILD_DIR=".build"
LAMBDA_DIR="../lambda/jobs/get_job_details"

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
zip -r get_job_details.zip . -q
cd ..

echo "👉 Updating Lambda code: $FUNCTION_NAME ..."
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://$BUILD_DIR/get_job_details.zip \
    --region us-east-2

echo "✅ Deployment complete!"
