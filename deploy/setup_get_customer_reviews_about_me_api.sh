#!/usr/bin/env bash
set -e

FUNC_NAME="get_customer_reviews_about_me"
AWS_REGION="us-east-2"
AWS_ACCOUNT_ID="008971679867"
API_ID="kfvf20j7j9"
AUTHORIZER_ID="z8zn33"

echo "🔗 Setting up Lambda integration for ${FUNC_NAME}..."

LAMBDA_ARN="arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:${FUNC_NAME}"

INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --api-id "${API_ID}" \
  --integration-type AWS_PROXY \
  --integration-uri "${LAMBDA_ARN}" \
  --payload-format-version "2.0" \
  --region "${AWS_REGION}" \
  --query 'IntegrationId' \
  --output text)

echo "✅ Created integration: ${INTEGRATION_ID}"

echo "📝 Creating route GET /customer/reviews-about-me..."
ROUTE_ID=$(aws apigatewayv2 get-routes \
  --api-id "${API_ID}" \
  --region "${AWS_REGION}" \
  --query "Items[?RouteKey=='GET /customer/reviews-about-me'].RouteId" \
  --output text)

if [ -n "${ROUTE_ID}" ] && [ "${ROUTE_ID}" != "None" ]; then
  aws apigatewayv2 update-route \
    --api-id "${API_ID}" \
    --route-id "${ROUTE_ID}" \
    --target "integrations/${INTEGRATION_ID}" \
    --authorization-type JWT \
    --authorizer-id "${AUTHORIZER_ID}" \
    --region "${AWS_REGION}" > /dev/null
  echo "✅ Updated existing route: ${ROUTE_ID}"
else
  ROUTE_ID=$(aws apigatewayv2 create-route \
    --api-id "${API_ID}" \
    --route-key "GET /customer/reviews-about-me" \
    --target "integrations/${INTEGRATION_ID}" \
    --authorization-type JWT \
    --authorizer-id "${AUTHORIZER_ID}" \
    --region "${AWS_REGION}" \
    --query 'RouteId' \
    --output text)
  echo "✅ Created route: ${ROUTE_ID}"
fi

echo "🔑 Adding Lambda permission..."

aws lambda add-permission \
  --function-name "${FUNC_NAME}" \
  --statement-id "apigatewayv2-invoke-${FUNC_NAME}-$(date +%s)" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*/*" \
  --region "${AWS_REGION}" > /dev/null

echo "🚀 Deploying API..."

aws apigatewayv2 create-deployment \
  --api-id "${API_ID}" \
  --stage-name prod \
  --description "Added GET /customer/reviews-about-me" \
  --region "${AWS_REGION}" > /dev/null

echo "✅ API Gateway setup complete!"
echo ""
echo "GET https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod/customer/reviews-about-me"
