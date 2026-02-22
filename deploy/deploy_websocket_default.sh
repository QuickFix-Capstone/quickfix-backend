#!/usr/bin/env bash
set -euo pipefail
FUNCTION_NAME="${WEBSOCKET_DEFAULT_FUNCTION_NAME:-websocket_default}"
./deploy/_deploy_websocket_lambda.sh "lambda/websocket/default" "${FUNCTION_NAME}"
