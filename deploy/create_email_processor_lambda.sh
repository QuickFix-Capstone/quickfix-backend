#!/bin/bash

# Create Lambda function for processing booking emails

LAMBDA_NAME="process-booking-emails"
REGION="us-east-1"
LAMBDA_DIR="lambda/email/process_booking_emails"

echo "⚡ Creating email processing Lambda function..."

# 1. Create IAM role for the Lambda
ROLE_NAME="ProcessBookingEmailsRole"
echo "🔐 Creating IAM role..."

TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

# Create role (ignore if exists)
aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document "$TRUST_POLICY" 2>/dev/null || echo "Role already exists"

# Attach basic execution policy
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Create custom policy for SES and SQS
LAMBDA_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "*"
    }
  ]
}'

aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name EmailProcessingPolicy \
    --policy-document "$LAMBDA_POLICY"

# Wait for role to be ready
echo "⏳ Waiting for IAM role to be ready..."
sleep 10

# Get role ARN
ROLE_ARN=$(aws iam get-role \
    --role-name $ROLE_NAME \
    --query 'Role.Arn' \
    --output text)

echo "✅ Role created: $ROLE_ARN"

# 2. Package the Lambda function
echo "📦 Packaging Lambda function..."

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
cp -r $LAMBDA_DIR/* $TEMP_DIR/
cp -r src/ $TEMP_DIR/

# Create zip file
cd $TEMP_DIR
zip -r $LAMBDA_NAME.zip . -x "__pycache__/*" "*.pyc" "test_*"
cd - > /dev/null

# 3. Create Lambda function
echo "🚀 Creating Lambda function..."

aws lambda create-function \
    --function-name $LAMBDA_NAME \
    --runtime python3.9 \
    --role $ROLE_ARN \
    --handler handler.handler \
    --zip-file fileb://$TEMP_DIR/$LAMBDA_NAME.zip \
    --timeout 60 \
    --memory-size 256 \
    --environment Variables="{SES_SENDER_EMAIL=$SES_SENDER_EMAIL,AWS_SES_REGION=$REGION}" \
    --region $REGION

echo "✅ Lambda function created successfully!"

# Clean up
rm -rf $TEMP_DIR

echo ""
echo "📋 Lambda function details:"
echo "Name: $LAMBDA_NAME"
echo "Role: $ROLE_ARN"
echo ""
echo "🔧 Next step: Connect SQS queue to this Lambda function"