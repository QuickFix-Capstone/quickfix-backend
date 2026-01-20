#!/usr/bin/env bash
# Configure AWS credentials for QuickFix deployment
# NOTE: Never commit real credentials. Use environment variables or AWS profiles.

set -e

# These should be set as environment variables, not hardcoded
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "❌ Error: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set as environment variables"
    echo ""
    echo "Usage:"
    echo "  export AWS_ACCESS_KEY_ID=your_access_key"
    echo "  export AWS_SECRET_ACCESS_KEY=your_secret_key"
    echo "  ./configure_aws.sh"
    exit 1
fi

AWS_REGION="${AWS_REGION:-us-east-2}"

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
