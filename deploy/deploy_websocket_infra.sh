#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-us-east-2}"
STACK_NAME="${WEBSOCKET_INFRA_STACK_NAME:-quickfix-websocket-phase1}"

aws cloudformation deploy \
  --template-file deploy/cloudformation/websocket_phase1_infra.yaml \
  --stack-name "${STACK_NAME}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "${AWS_REGION}" \
  --no-cli-pager

echo "✅ Deployed stack: ${STACK_NAME}"
aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${AWS_REGION}" \
  --query 'Stacks[0].Outputs' \
  --output table
