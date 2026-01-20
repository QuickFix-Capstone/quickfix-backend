#!/usr/bin/env bash
# Configure AWS credentials for QuickFix deployment

set -e

AWS_ACCESS_KEY_ID="YOUR_AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_ACCESS_KEY"
AWS_REGION="us-east-2"

echo "🔐 Configuring AWS credentials..."

# Configure AWS CLI
aws configure set aws_access_key_id "$AWS_ACCESS_KEY_ID"
aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY"
aws configure set region "$AWS_REGION"
aws configure set output "json"

echo "✅ AWS credentials configured successfully!"
echo ""
echo "Verifying configuration..."
aws configure list

echo ""
echo "Testing AWS connection..."
aws sts get-caller-identity
