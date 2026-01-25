#!/bin/bash

# Create SQS queue for async email processing

REGION="us-east-1"
QUEUE_NAME="booking-email-queue"

echo "📬 Creating SQS queue for email processing..."

# Create the queue
QUEUE_URL=$(aws sqs create-queue \
    --queue-name $QUEUE_NAME \
    --region $REGION \
    --attributes '{
        "VisibilityTimeoutSeconds": "300",
        "MessageRetentionPeriod": "1209600",
        "ReceiveMessageWaitTimeSeconds": "20"
    }' \
    --query 'QueueUrl' \
    --output text)

echo "✅ Queue created successfully!"
echo "Queue URL: $QUEUE_URL"

# Get queue ARN
QUEUE_ARN=$(aws sqs get-queue-attributes \
    --queue-url $QUEUE_URL \
    --attribute-names QueueArn \
    --query 'Attributes.QueueArn' \
    --output text)

echo "Queue ARN: $QUEUE_ARN"

# Save to environment file
echo "EMAIL_QUEUE_URL=$QUEUE_URL" >> .env
echo "EMAIL_QUEUE_ARN=$QUEUE_ARN" >> .env

echo ""
echo "🔧 Next steps:"
echo "1. Add EMAIL_QUEUE_URL to your create_booking Lambda environment variables"
echo "2. Add SQS send permissions to your create_booking Lambda role"
echo "3. Create the email processing Lambda function"