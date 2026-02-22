#!/usr/bin/env bash
set -euo pipefail
FUNCTION_NAME="${WEBSOCKET_SEND_MESSAGE_FUNCTION_NAME:-websocket_send_message}"
./deploy/_deploy_websocket_lambda.sh "lambda/websocket/send_message" "${FUNCTION_NAME}"
