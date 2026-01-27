#!/usr/bin/env bash
set -e

API_ID="kfvf20j7j9"
AWS_REGION="us-east-2"
LAMBDA_NAME="create_booking_image"
ROUTE_KEY="POST /bookings/{booking_id}/images"
AUTHORIZER_ID="z8zn33"  # QuickFixCustomerAuth
AWS_ACCOUNT_ID="008971679867"

echo "🔧 Setting up API Gateway route for ${LAMBDA_NAME}..."

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

# Create route
echo "👉 Creating route..."
ROUTE_ID=$(aws apigatewayv2 create-route \
  --api-id "$API_ID" \
  --route-key "$ROUTE_KEY" \
  --target "integrations/${INTEGRATION_ID}" \
  --authorizer-id "$AUTHORIZER_ID" \
  --authorization-type JWT \
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
  --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*/*/bookings/{booking_id}/images" \
  --region "$AWS_REGION" 2>&1 | grep -v "ResourceConflictException" || true

echo "✅ Route configured successfully!"
echo ""
echo "📋 Route Details:"
echo "   Route: ${ROUTE_KEY}"
echo "   Endpoint: https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/bookings/{booking_id}/images"
echo "   Authorizer: QuickFixCustomerAuth (JWT)"
