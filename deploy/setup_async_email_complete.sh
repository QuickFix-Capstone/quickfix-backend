#!/bin/bash

# Complete setup for async email processing
# This script runs all the setup steps in order

set -e

echo "🚀 Setting up async email processing for QuickFix..."
echo "=================================================="

# Check required environment variables
if [ -z "$SES_SENDER_EMAIL" ]; then
    echo "❌ Error: SES_SENDER_EMAIL environment variable is required"
    echo "   Set it with: export SES_SENDER_EMAIL=your-verified-email@domain.com"
    exit 1
fi

echo "📧 Using SES sender email: $SES_SENDER_EMAIL"
echo ""

# Step 1: Create SQS queue
echo "Step 1: Creating SQS queue..."
bash deploy/create_email_queue.sh
echo ""

# Step 2: Create email processing Lambda
echo "Step 2: Creating email processing Lambda..."
bash deploy/create_email_processor_lambda.sh
echo ""

# Step 3: Connect queue to Lambda
echo "Step 3: Connecting SQS queue to Lambda..."
bash deploy/connect_queue_to_lambda.sh
echo ""

# Step 4: Update create_booking Lambda permissions
echo "Step 4: Updating create_booking Lambda permissions..."
echo "⚠️  Note: You may need to update the CREATE_BOOKING_LAMBDA variable in the script"
echo "   Current value: create-booking"
read -p "Press Enter to continue or Ctrl+C to edit the script first..."
bash deploy/update_create_booking_permissions.sh
echo ""

echo "✅ Async email setup complete!"
echo ""
echo "📋 What was created:"
echo "- SQS Queue: booking-email-queue"
echo "- Lambda Function: process-booking-emails"
echo "- IAM Role: ProcessBookingEmailsRole"
echo "- Event Source Mapping: SQS → Lambda"
echo ""
echo "🔧 Next steps:"
echo "1. Replace your create_booking handler.py with handler_async.py"
echo "2. Test the booking creation to verify emails are sent asynchronously"
echo "3. Monitor CloudWatch logs for both Lambda functions"
echo ""
echo "📊 Monitoring:"
echo "- SQS Queue metrics in CloudWatch"
echo "- Lambda function logs in CloudWatch"
echo "- SES sending statistics in SES console"