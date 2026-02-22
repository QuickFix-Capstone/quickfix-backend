#!/usr/bin/env bash
set -euo pipefail
FUNCTION_NAME="${WEBSOCKET_TYPING_FUNCTION_NAME:-websocket_typing}"
./deploy/_deploy_websocket_lambda.sh "lambda/websocket/typing" "${FUNCTION_NAME}"
