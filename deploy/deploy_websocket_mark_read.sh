#!/usr/bin/env bash
set -euo pipefail
FUNCTION_NAME="${WEBSOCKET_MARK_READ_FUNCTION_NAME:-websocket_mark_read}"
./deploy/_deploy_websocket_lambda.sh "lambda/websocket/mark_read" "${FUNCTION_NAME}"
