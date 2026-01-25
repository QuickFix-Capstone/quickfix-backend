#!/bin/bash

# Connect SQS queue to Lambda function for automatic processing

LAMBDA_NAME="process-booking-emails"
QUEUE_NAME="booking-email-queue"
REGION="us-east-1"

echo "🔗 Connecting SQS queue to Lambda function..."

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

echo "Queue ARN: $QUEUE_ARN"

# Create event source mapping
aws lambda create-event-source-mapping \
    --event-source-arn $QUEUE_ARN \
    --function-name $LAMBDA_NAME \
    --batch-size 10 \
    --maximum-batching-window-in-seconds 5 \
    --region $REGION

echo "✅ SQS queue connected to Lambda function!"
echo ""
echo "📋 Setup complete:"
echo "- SQS Queue: $QUEUE_NAME"
echo "- Lambda: $LAMBDA_NAME"
echo "- Messages sent to queue will automatically trigger Lambda"