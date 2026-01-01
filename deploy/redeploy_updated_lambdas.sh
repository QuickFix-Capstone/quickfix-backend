#!/usr/bin/env bash
# Redeploy customer Lambda functions that were updated for avatar_url support

set -e

echo "🚀 Redeploying updated customer Lambda functions..."
echo ""

echo "📦 1/2 Deploying get_customer..."
./deploy_get_customer.sh
echo ""

echo "📦 2/2 Deploying update_customer..."
./deploy_update_customer.sh
echo ""

echo "✅ All customer Lambda functions redeployed successfully!"
echo ""
echo "Updated functions now support avatar_url field."
