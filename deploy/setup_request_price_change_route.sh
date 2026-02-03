#!/usr/bin/env bash
set -e

API_ID="kfvf20j7j9"
AWS_REGION="us-east-2"
LAMBDA_NAME="request_price_change"
ROUTE_KEY="POST /jobs/{jobId}/price-change-requests"
AWS_ACCOUNT_ID="008971679867"

# Optional: Set authorizer if needed (you said you'll handle this)
# AUTHORIZER_ID="z8zn33"  # QuickFixCustomerAuth or provider auth
# AUTHORIZATION_TYPE="JWT"

echo "🔧 Setting up API Gateway route for ${LAMBDA_NAME}..."
echo "============================================"

# Get Lambda ARN
LAMBDA_ARN="arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:${LAMBDA_NAME}"
echo "Lambda ARN: ${LAMBDA_ARN}"

# Create integration
echo "👉 Creating integration..."
INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --api-id "$API_ID" \
  --integration-type AWS_PROXY \
  --integration-uri "$LAMBDA_ARN" \
  --payload-format-version 2.0 \
  --region "$AWS_REGION" \
  --query 'IntegrationId' \
  --output text)

echo "Integration ID: ${INTEGRATION_ID}"

# Create route WITHOUT authorizer (you'll add it yourself)
echo "👉 Creating route (without authorizer)..."
ROUTE_ID=$(aws apigatewayv2 create-route \
  --api-id "$API_ID" \
  --route-key "$ROUTE_KEY" \
  --target "integrations/${INTEGRATION_ID}" \
  --region "$AWS_REGION" \
  --query 'RouteId' \
  --output text)

echo "Route ID: ${ROUTE_ID}"

# Grant API Gateway permission to invoke Lambda
echo "👉 Granting API Gateway permission to invoke Lambda..."
aws lambda add-permission \
  --function-name "$LAMBDA_NAME" \
  --statement-id "apigateway-${ROUTE_ID}" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*/*/jobs/{jobId}/price-change-requests" \
  --region "$AWS_REGION" 2>&1 | grep -v "ResourceConflictException" || true

echo ""
echo "✅ Route configured successfully!"
echo "============================================"
echo "📋 Route Details:"
echo "   Route: ${ROUTE_KEY}"
echo "   Endpoint: https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/jobs/{jobId}/price-change-requests"
echo "   Authorization: NONE (configure manually if needed)"
echo ""
echo "🔐 To add authorization, run:"
echo "   aws apigatewayv2 update-route \\"
echo "     --api-id ${API_ID} \\"
echo "     --route-id ${ROUTE_ID} \\"
echo "     --authorizer-id YOUR_AUTHORIZER_ID \\"
echo "     --authorization-type JWT \\"
echo "     --region ${AWS_REGION}"
echo ""
