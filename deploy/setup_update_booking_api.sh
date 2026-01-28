#!/usr/bin/env bash
# Setup API Gateway route for update_booking Lambda

set -e

API_ID="kfvf20j7j9"
LAMBDA_ARN="arn:aws:lambda:us-east-2:008971679867:function:update_booking"
AWS_REGION="us-east-2"
ROUTE_KEY="PUT /customer/bookings/{booking_id}"

echo "🔧 Setting up API Gateway route for update_booking..."

# Create integration
echo "Creating Lambda integration..."
INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --api-id "${API_ID}" \
  --integration-type AWS_PROXY \
  --integration-uri "${LAMBDA_ARN}" \
  --payload-format-version "2.0" \
  --region "${AWS_REGION}" \
  --query 'IntegrationId' \
  --output text)

echo "Integration created: ${INTEGRATION_ID}"

# Create route
echo "Creating route: ${ROUTE_KEY}..."
ROUTE_ID=$(aws apigatewayv2 create-route \
  --api-id "${API_ID}" \
  --route-key "${ROUTE_KEY}" \
  --target "integrations/${INTEGRATION_ID}" \
  --authorization-type JWT \
  --authorizer-id "rvxfhf" \
  --region "${AWS_REGION}" \
  --query 'RouteId' \
  --output text)

echo "Route created: ${ROUTE_ID}"

# Grant API Gateway permission to invoke Lambda
echo "Granting API Gateway permission to invoke Lambda..."
aws lambda add-permission \
  --function-name update_booking \
  --statement-id apigateway-update-booking-$(date +%s) \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${AWS_REGION}:008971679867:${API_ID}/*/*/customer/bookings/*" \
  --region "${AWS_REGION}" || echo "Permission may already exist"

echo ""
echo "✅ API Gateway route setup complete!"
echo "Route: ${ROUTE_KEY}"
echo "Endpoint: https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/customer/bookings/{booking_id}"
