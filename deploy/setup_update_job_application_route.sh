#!/usr/bin/env bash
set -e

API_ID="kfvf20j7j9"
AWS_REGION="us-east-2"
AWS_ACCOUNT_ID="008971679867"
LAMBDA_NAME="update_job_application"
ROUTE_KEY="PUT /job/{job_id}/applications/{application_id}/update"
PROVIDER_AUTHORIZER_ID="wd1mnf"

echo "Setting up API Gateway route for ${LAMBDA_NAME}..."

LAMBDA_ARN="arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:${LAMBDA_NAME}"

# Reuse existing integration if already configured for this lambda.
INTEGRATIONS_JSON=$(aws apigatewayv2 get-integrations \
  --api-id "${API_ID}" \
  --region "${AWS_REGION}" \
  --output json)
INTEGRATION_ID=$(INTEGRATIONS_JSON="${INTEGRATIONS_JSON}" python3 -c "import os, json; items=json.loads(os.environ['INTEGRATIONS_JSON']).get('Items', []); matches=[i.get('IntegrationId') for i in items if i.get('IntegrationUri') == '${LAMBDA_ARN}']; print(matches[0] if matches else '')")

if [ -z "${INTEGRATION_ID}" ]; then
  echo "Creating integration..."
  INTEGRATION_ID=$(aws apigatewayv2 create-integration \
    --api-id "${API_ID}" \
    --integration-type AWS_PROXY \
    --integration-uri "${LAMBDA_ARN}" \
    --payload-format-version 2.0 \
    --region "${AWS_REGION}" \
    --query 'IntegrationId' \
    --output text)
else
  echo "Using existing integration: ${INTEGRATION_ID}"
fi

# Create route if missing.
ROUTES_JSON=$(aws apigatewayv2 get-routes \
  --api-id "${API_ID}" \
  --region "${AWS_REGION}" \
  --output json)
EXISTING_ROUTE_ID=$(ROUTES_JSON="${ROUTES_JSON}" python3 -c "import os, json; items=json.loads(os.environ['ROUTES_JSON']).get('Items', []); matches=[r.get('RouteId') for r in items if r.get('RouteKey') == '${ROUTE_KEY}']; print(matches[0] if matches else '')")

if [ -z "${EXISTING_ROUTE_ID}" ]; then
  echo "Creating route..."
  ROUTE_ID=$(aws apigatewayv2 create-route \
    --api-id "${API_ID}" \
    --route-key "${ROUTE_KEY}" \
    --target "integrations/${INTEGRATION_ID}" \
    --authorizer-id "${PROVIDER_AUTHORIZER_ID}" \
    --authorization-type JWT \
    --region "${AWS_REGION}" \
    --query 'RouteId' \
    --output text)
else
  ROUTE_ID="${EXISTING_ROUTE_ID}"
  echo "Route already exists: ${ROUTE_ID}"
fi

# Deploy route changes to prod stage (AutoDeploy is disabled on this API).
aws apigatewayv2 create-deployment \
  --api-id "${API_ID}" \
  --stage-name "prod" \
  --region "${AWS_REGION}" >/dev/null

STATEMENT_ID="apigateway-update-job-application"
set +e
aws lambda add-permission \
  --function-name "${LAMBDA_NAME}" \
  --statement-id "${STATEMENT_ID}" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*/*/job/*/applications/*/update" \
  --region "${AWS_REGION}" >/tmp/update_job_application_permission.log 2>&1
PERM_RC=$?
set -e

if [ ${PERM_RC} -ne 0 ]; then
  if rg -q "ResourceConflictException" /tmp/update_job_application_permission.log; then
    echo "Lambda permission already exists."
  else
    cat /tmp/update_job_application_permission.log
    exit ${PERM_RC}
  fi
fi

echo "Route configured successfully."
echo "Endpoint: https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod/job/{job_id}/applications/{application_id}/update"
