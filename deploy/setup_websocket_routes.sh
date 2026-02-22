#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-us-east-2}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
API_NAME="${WEBSOCKET_API_NAME:-quickfix-websocket}"
STAGE_NAME="${WEBSOCKET_STAGE:-prod}"
API_ID="${WEBSOCKET_API_ID:-}"

# Default function names; override with env vars if your Lambda names differ.
CONNECT_FN="${WEBSOCKET_CONNECT_FUNCTION_NAME:-websocket_connect}"
DISCONNECT_FN="${WEBSOCKET_DISCONNECT_FUNCTION_NAME:-websocket_disconnect}"
DEFAULT_FN="${WEBSOCKET_DEFAULT_FUNCTION_NAME:-websocket_default}"
PING_FN="${WEBSOCKET_PING_FUNCTION_NAME:-websocket_ping}"
SEND_MESSAGE_FN="${WEBSOCKET_SEND_MESSAGE_FUNCTION_NAME:-websocket_send_message}"
GET_MESSAGES_FN="${WEBSOCKET_GET_MESSAGES_FUNCTION_NAME:-websocket_get_messages}"
GET_CONVERSATIONS_FN="${WEBSOCKET_GET_CONVERSATIONS_FUNCTION_NAME:-websocket_get_conversations}"
MARK_READ_FN="${WEBSOCKET_MARK_READ_FUNCTION_NAME:-websocket_mark_read}"
TYPING_FN="${WEBSOCKET_TYPING_FUNCTION_NAME:-websocket_typing}"

if [ -z "${API_ID}" ]; then
  API_ID=$(aws apigatewayv2 get-apis \
    --region "${AWS_REGION}" \
    --query "Items[?Name=='${API_NAME}' && ProtocolType=='WEBSOCKET']|[0].ApiId" \
    --output text)

  if [ -z "${API_ID}" ] || [ "${API_ID}" = "None" ]; then
    echo "🆕 Creating WebSocket API: ${API_NAME}"
    API_ID=$(aws apigatewayv2 create-api \
      --name "${API_NAME}" \
      --protocol-type WEBSOCKET \
      --route-selection-expression '$request.body.action' \
      --region "${AWS_REGION}" \
      --query 'ApiId' \
      --output text)
  else
    echo "🔍 Reusing existing WebSocket API: ${API_ID}"
  fi
else
  echo "🔍 Using provided WebSocket API ID: ${API_ID}"
fi

ensure_integration() {
  local route_key="$1"
  local function_name="$2"

  local lambda_arn="arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:${function_name}"
  local integration_id

  integration_id=$(aws apigatewayv2 get-integrations \
    --api-id "${API_ID}" \
    --region "${AWS_REGION}" \
    --query "Items[?IntegrationUri=='${lambda_arn}']|[0].IntegrationId" \
    --output text)

  if [ -z "${integration_id}" ] || [ "${integration_id}" = "None" ]; then
    integration_id=$(aws apigatewayv2 create-integration \
      --api-id "${API_ID}" \
      --integration-type AWS_PROXY \
      --integration-uri "${lambda_arn}" \
      --payload-format-version 1.0 \
      --region "${AWS_REGION}" \
      --query 'IntegrationId' \
      --output text)
    echo "✅ Created integration for ${route_key}: ${integration_id}"
  else
    echo "✅ Reusing integration for ${route_key}: ${integration_id}"
  fi

  local route_id
  route_id=$(aws apigatewayv2 get-routes \
    --api-id "${API_ID}" \
    --region "${AWS_REGION}" \
    --query "Items[?RouteKey=='${route_key}']|[0].RouteId" \
    --output text)

  if [ -z "${route_id}" ] || [ "${route_id}" = "None" ]; then
    route_id=$(aws apigatewayv2 create-route \
      --api-id "${API_ID}" \
      --route-key "${route_key}" \
      --target "integrations/${integration_id}" \
      --region "${AWS_REGION}" \
      --query 'RouteId' \
      --output text)
    echo "✅ Created route ${route_key}: ${route_id}"
  else
    aws apigatewayv2 update-route \
      --api-id "${API_ID}" \
      --route-id "${route_id}" \
      --target "integrations/${integration_id}" \
      --region "${AWS_REGION}" >/dev/null
    echo "✅ Updated route ${route_key}: ${route_id}"
  fi

  aws lambda add-permission \
    --function-name "${function_name}" \
    --statement-id "apigatewayv2-ws-${route_key//[^a-zA-Z0-9]/-}-$(date +%s)" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*" \
    --region "${AWS_REGION}" >/dev/null 2>&1 || true
}

ensure_integration '$connect' "${CONNECT_FN}"
ensure_integration '$disconnect' "${DISCONNECT_FN}"
ensure_integration '$default' "${DEFAULT_FN}"
ensure_integration 'ping' "${PING_FN}"
ensure_integration 'sendMessage' "${SEND_MESSAGE_FN}"
ensure_integration 'getMessages' "${GET_MESSAGES_FN}"
ensure_integration 'getConversations' "${GET_CONVERSATIONS_FN}"
ensure_integration 'markRead' "${MARK_READ_FN}"
ensure_integration 'typing' "${TYPING_FN}"

LOG_GROUP_NAME="${WEBSOCKET_LOG_GROUP_NAME:-/aws/apigateway/${API_NAME}}"
aws logs create-log-group --log-group-name "${LOG_GROUP_NAME}" --region "${AWS_REGION}" >/dev/null 2>&1 || true
aws logs put-retention-policy \
  --log-group-name "${LOG_GROUP_NAME}" \
  --retention-in-days "${WEBSOCKET_LOG_RETENTION_DAYS:-14}" \
  --region "${AWS_REGION}" >/dev/null 2>&1 || true

LOG_DEST_ARN="arn:aws:logs:${AWS_REGION}:${AWS_ACCOUNT_ID}:log-group:${LOG_GROUP_NAME}"
LOG_FORMAT='$context.requestId $context.routeKey $context.status $context.integration.status $context.error.message $context.identity.sourceIp $context.connectedAt'

STAGE_EXISTS=$(aws apigatewayv2 get-stages \
  --api-id "${API_ID}" \
  --region "${AWS_REGION}" \
  --query "Items[?StageName=='${STAGE_NAME}']|length(@)" \
  --output text)

if [ "${STAGE_EXISTS}" = "0" ]; then
  aws apigatewayv2 create-stage \
    --api-id "${API_ID}" \
    --stage-name "${STAGE_NAME}" \
    --auto-deploy \
    --access-log-settings "DestinationArn=${LOG_DEST_ARN},Format=${LOG_FORMAT}" \
    --default-route-settings "DetailedMetricsEnabled=true,DataTraceEnabled=true,LoggingLevel=INFO" \
    --region "${AWS_REGION}" >/dev/null
  echo "✅ Created stage ${STAGE_NAME} with logging"
else
  aws apigatewayv2 update-stage \
    --api-id "${API_ID}" \
    --stage-name "${STAGE_NAME}" \
    --access-log-settings "DestinationArn=${LOG_DEST_ARN},Format=${LOG_FORMAT}" \
    --default-route-settings "DetailedMetricsEnabled=true,DataTraceEnabled=true,LoggingLevel=INFO" \
    --region "${AWS_REGION}" >/dev/null
  echo "✅ Updated stage ${STAGE_NAME} logging settings"
fi

aws apigatewayv2 create-deployment \
  --api-id "${API_ID}" \
  --stage-name "${STAGE_NAME}" \
  --region "${AWS_REGION}" >/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ WebSocket routes configured"
echo "API ID: ${API_ID}"
echo "WS URL: wss://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/${STAGE_NAME}"
echo "Log group: ${LOG_GROUP_NAME}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
