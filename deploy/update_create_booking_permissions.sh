#!/bin/bash

# Add SQS permissions to create_booking Lambda function

CREATE_BOOKING_LAMBDA="create-booking"  # Replace with your actual Lambda name
QUEUE_NAME="booking-email-queue"
REGION="us-east-1"

echo "🔐 Adding SQS permissions to create_booking Lambda..."

# Get queue ARN
QUEUE_URL=$(aws sqs get-queue-url \
    --queue-name $QUEUE_NAME \
    --region $REGION \
    --query 'QueueUrl' \
    --output text)

QUEUE_ARN=$(aws sqs get-queue-attributes \
    --queue-url $QUEUE_URL \
    --attribute-names QueueArn \
    --query 'Attributes.QueueArn' \
    --output text)

# Get the Lambda's role name
LAMBDA_ROLE=$(aws lambda get-function \
    --function-name $CREATE_BOOKING_LAMBDA \
    --query 'Configuration.Role' \
    --output text)

ROLE_NAME=$(echo $LAMBDA_ROLE | cut -d'/' -f2)

echo "Lambda role: $ROLE_NAME"

# Create SQS policy for the role
SQS_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage",
        "sqs:GetQueueUrl"
      ],
      "Resource": "'$QUEUE_ARN'"
    }
  ]
}'

# Add the policy to the role
aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name SendEmailQueuePolicy \
    --policy-document "$SQS_POLICY"

# Update Lambda environment variables
aws lambda update-function-configuration \
    --function-name $CREATE_BOOKING_LAMBDA \
    --environment Variables="{EMAIL_QUEUE_URL=$QUEUE_URL}" \
    --region $REGION

echo "✅ Permissions updated successfully!"
echo ""
echo "📋 Added to $CREATE_BOOKING_LAMBDA:"
echo "- SQS send permissions for: $QUEUE_ARN"
echo "- Environment variable: EMAIL_QUEUE_URL=$QUEUE_URL"