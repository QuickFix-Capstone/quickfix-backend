#!/usr/bin/env bash
set -euo pipefail
FUNCTION_NAME="${WEBSOCKET_GET_CONVERSATIONS_FUNCTION_NAME:-websocket_get_conversations}"
./deploy/_deploy_websocket_lambda.sh "lambda/websocket/get_conversations" "${FUNCTION_NAME}"
