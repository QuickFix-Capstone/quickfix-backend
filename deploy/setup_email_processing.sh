#!/bin/bash

# Setup SQS queue and email processing Lambda for async email handling

set -e

REGION="us-east-1"
QUEUE_NAME="booking-email-queue"
LAMBDA_NAME="process-booking-emails"
LAMBDA_DIR="lambda/email/process_booking_emails"

echo "🚀 Setting up async email processing infrastructure..."

# 1. Create SQS queue
echo "📬 Creating SQS queue: $QUEUE_NAME"
QUEUE_URL=$(aws sqs create-queue \
    --queue-name $QUEUE_NAME \
    --region $REGION \
    --attributes VisibilityTimeoutSeconds=300,MessageRetentionPeriod=1209600 \
    --query 'QueueUrl' \
    --output text)

echo "✅ Queue created: $QUEUE_URL"

# 2. Get queue ARN
QUEUE_ARN=$(aws sqs get-queue-attributes \
    --queue-url $QUEUE_URL \
    --attribute-names QueueArn \
    --query 'Attributes.QueueArn' \
    --output text)

echo "📋 Queue ARN: $QUEUE_ARN"

# 3. Create Lambda execution role
ROLE_NAME="ProcessBookingEmailsRole"
echo "🔐 Creating IAM role: $ROLE_NAME"

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

aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document "$TRUST_POLICY" \
    --region $REGION || echo "Role may already exist"

# 4. Attach basic Lambda execution policy
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# 5. Create SES policy for the role
SES_POLICY='{
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
      "Resource": "'$QUEUE_ARN'"
    }
  ]
}'

aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name ProcessBookingEmailsPolicy \
    --policy-document "$SES_POLICY"

# 6. Get role ARN
ROLE_ARN=$(aws iam get-role \
    --role-name $ROLE_NAME \
    --query 'Role.Arn' \
    --output text)

echo "✅ Role ARN: $ROLE_ARN"

# 7. Package Lambda function
echo "📦 Packaging Lambda function..."
cd $LAMBDA_DIR
zip -r ../../../$LAMBDA_NAME.zip . -x "__pycache__/*" "*.pyc"
cd ../../..

# 8. Create Lambda function
echo "⚡ Creating Lambda function: $LAMBDA_NAME"
aws lambda create-function \
    --function-name $LAMBDA_NAME \
    --runtime python3.9 \
    --role $ROLE_ARN \
    --handler handler.handler \
    --zip-file fileb://$LAMBDA_NAME.zip \
    --timeout 60 \
    --memory-size 256 \
    --environment Variables="{SES_SENDER_EMAIL=$SES_SENDER_EMAIL,AWS_SES_REGION=$REGION}" \
    --region $REGION || echo "Lambda may already exist, updating..."

# Update if exists
aws lambda update-function-code \
    --function-name $LAMBDA_NAME \
    --zip-file fileb://$LAMBDA_NAME.zip \
    --region $REGION

# 9. Create event source mapping (SQS trigger)
echo "🔗 Creating SQS trigger for Lambda..."
aws lambda create-event-source-mapping \
    --event-source-arn $QUEUE_ARN \
    --function-name $LAMBDA_NAME \
    --batch-size 10 \
    --region $REGION || echo "Event source mapping may already exist"

# 10. Clean up
rm $LAMBDA_NAME.zip

echo "✅ Email processing setup complete!"
echo ""
echo "📋 Configuration Summary:"
echo "Queue URL: $QUEUE_URL"
echo "Queue ARN: $QUEUE_ARN"
echo "Lambda: $LAMBDA_NAME"
echo ""
echo "🔧 Next steps:"
echo "1. Set EMAIL_QUEUE_URL environment variable in your create_booking Lambda:"
echo "   EMAIL_QUEUE_URL=$QUEUE_URL"
echo ""
echo "2. Add SQS permissions to your create_booking Lambda role:"
echo "   - sqs:SendMessage on $QUEUE_ARN"
echo ""
echo "3. Update your create_booking handler to use the async version"