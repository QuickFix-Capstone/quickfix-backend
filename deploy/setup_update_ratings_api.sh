#!/usr/bin/env bash
# Setup API Gateway endpoint for update_ratings Lambda with IAM authentication
# This creates an INTERNAL API that requires AWS credentials (not public)

set -e

FUNC_NAME="update_ratings"
AWS_REGION="us-east-2"
AWS_ACCOUNT_ID="008971679867"
API_ID="kfvf20j7j9"  # Existing HTTP API Gateway ID

echo "🔍 Using existing API Gateway: ${API_ID}"
echo "🔐 Setting up INTERNAL endpoint with IAM authentication"
echo ""

# Step 1: Create Lambda integration
echo "🔗 Creating Lambda integration..."

LAMBDA_ARN="arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:${FUNC_NAME}"

INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --api-id "${API_ID}" \
  --integration-type AWS_PROXY \
  --integration-uri "${LAMBDA_ARN}" \
  --payload-format-version 2.0 \
  --region "${AWS_REGION}" \
  --query 'IntegrationId' \
  --output text)

echo "✅ Created integration: ${INTEGRATION_ID}"

# Step 2: Create route with IAM authorization
echo "📝 Creating route: POST /internal/update-ratings..."
echo "   (Using AWS_IAM authorization for internal use only)"

ROUTE_ID=$(aws apigatewayv2 create-route \
  --api-id "${API_ID}" \
  --route-key "POST /internal/update-ratings" \
  --authorization-type AWS_IAM \
  --target "integrations/${INTEGRATION_ID}" \
  --region "${AWS_REGION}" \
  --query 'RouteId' \
  --output text 2>/dev/null || echo "")

if [ -z "$ROUTE_ID" ]; then
  echo "⚠️  Route may already exist, trying to update..."

  # Get existing route ID
  ROUTE_ID=$(aws apigatewayv2 get-routes \
    --api-id "${API_ID}" \
    --region "${AWS_REGION}" \
    --query "Items[?RouteKey=='POST /internal/update-ratings'].RouteId" \
    --output text)

  if [ -n "$ROUTE_ID" ]; then
    # Update existing route
    aws apigatewayv2 update-route \
      --api-id "${API_ID}" \
      --route-id "${ROUTE_ID}" \
      --authorization-type AWS_IAM \
      --target "integrations/${INTEGRATION_ID}" \
      --region "${AWS_REGION}"
    echo "✅ Updated existing route: ${ROUTE_ID}"
  fi
else
  echo "✅ Created route: ${ROUTE_ID}"
fi

# Step 3: Add Lambda permission
echo "🔑 Adding Lambda invoke permission..."

aws lambda add-permission \
  --function-name "${FUNC_NAME}" \
  --statement-id "apigatewayv2-invoke-$(date +%s)" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*/*/internal/update-ratings" \
  --region "${AWS_REGION}" 2>/dev/null || echo "⚠️  Permission may already exist"

echo "✅ Lambda permission added"

# Step 4: Deploy to prod stage
echo "🚀 Deploying to prod stage..."

aws apigatewayv2 create-deployment \
  --api-id "${API_ID}" \
  --stage-name prod \
  --region "${AWS_REGION}" > /dev/null

echo "✅ Deployment complete"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ INTERNAL API Gateway setup complete!"
echo ""
echo "📍 Internal API Endpoint:"
echo "   POST https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod/internal/update-ratings"
echo ""
echo "🔐 Authentication: AWS_IAM (Requires AWS Credentials)"
echo "   This endpoint can ONLY be called by:"
echo "   • Other Lambda functions (using AWS SDK with IAM role)"
echo "   • AWS CLI (with configured credentials)"
echo "   • Applications with AWS IAM credentials"
echo ""
echo "❌ This endpoint is NOT publicly accessible"
echo "❌ JWT tokens will NOT work (requires AWS signature)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Example 1: Call from another Lambda function"
echo "   import boto3"
echo "   import json"
echo "   "
echo "   # Using Lambda SDK (already authenticated via execution role)"
echo "   lambda_client = boto3.client('lambda')"
echo "   response = lambda_client.invoke("
echo "       FunctionName='update_ratings',"
echo "       InvocationType='Event',"
echo "       Payload=json.dumps({"
echo "           'reviewee_id': 1,"
echo "           'reviewee_type': 'provider'"
echo "       })"
echo "   )"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Example 2: Call via HTTP with AWS SigV4 signing"
echo "   import requests"
echo "   from requests_aws4auth import AWS4Auth"
echo "   import boto3"
echo "   "
echo "   # Get AWS credentials"
echo "   credentials = boto3.Session().get_credentials()"
echo "   auth = AWS4Auth("
echo "       credentials.access_key,"
echo "       credentials.secret_key,"
echo "       '${AWS_REGION}',"
echo "       'execute-api',"
echo "       session_token=credentials.token"
echo "   )"
echo "   "
echo "   # Make authenticated request"
echo "   response = requests.post("
echo "       'https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod/internal/update-ratings',"
echo "       auth=auth,"
echo "       json={'reviewee_id': 1, 'reviewee_type': 'provider'}"
echo "   )"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Recommended: Use Lambda-to-Lambda invocation instead of HTTP"
echo "   (It's simpler, faster, and doesn't require SigV4 signing)"
echo ""
