#!/usr/bin/env bash
set -euo pipefail
FUNCTION_NAME="${WEBSOCKET_GET_MESSAGES_FUNCTION_NAME:-websocket_get_messages}"
./deploy/_deploy_websocket_lambda.sh "lambda/websocket/get_messages" "${FUNCTION_NAME}"
