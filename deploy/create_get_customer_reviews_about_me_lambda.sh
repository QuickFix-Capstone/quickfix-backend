#!/bin/bash

# Script to create and deploy the get_customer_reviews_about_me Lambda function
# This endpoint returns reviews that providers have written ABOUT the customer

set -e

FUNCTION_NAME="get_customer_reviews_about_me"
HANDLER="handler.handler"
RUNTIME="python3.11"
ROLE_ARN="arn:aws:iam::008971679867:role/service-role/create_customer-role-qch33m23"
REGION="us-east-2"

# Database configuration (align with shared src.db.rds_main)
MYSQL_HOST="quickfix-mysql.cno624c2aarh.us-east-2.rds.amazonaws.com"
MYSQL_USER="admin"
MYSQL_DB="quickfix"
MYSQL_PORT="3306"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-QuickFix123!}"

echo "=================================================="
echo "Deploying Lambda: $FUNCTION_NAME"
echo "=================================================="

# Create build directory
BUILD_DIR="deploy/.build/$FUNCTION_NAME"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "📦 Copying Lambda code..."
cp lambda/reviews/get_customer_reviews_about_me/handler.py "$BUILD_DIR/"

# Copy shared database module
echo "📦 Copying shared database module..."
mkdir -p "$BUILD_DIR/src/db"
cp -r src/db/* "$BUILD_DIR/src/db/"

# Create __init__.py files
touch "$BUILD_DIR/src/__init__.py"
touch "$BUILD_DIR/src/db/__init__.py"

# Install dependencies if requirements.txt exists
if [ -f "lambda/reviews/get_customer_reviews_about_me/requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip install -r lambda/reviews/get_customer_reviews_about_me/requirements.txt -t "$BUILD_DIR/"
fi

# Install pymysql
echo "📦 Installing pymysql..."
pip install pymysql -t "$BUILD_DIR/"

# Create deployment package
echo "📦 Creating deployment package..."
cd "$BUILD_DIR"
zip -r "../${FUNCTION_NAME}.zip" . -q
cd - > /dev/null

echo "☁️  Checking if Lambda function exists..."
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" 2>/dev/null; then
    echo "🔄 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://deploy/.build/${FUNCTION_NAME}.zip" \
        --region "$REGION"
    
    echo "⚙️  Updating function configuration..."
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --handler "$HANDLER" \
        --runtime "$RUNTIME" \
        --timeout 30 \
        --memory-size 256 \
        --environment "Variables={MYSQL_HOST=$MYSQL_HOST,MYSQL_USER=$MYSQL_USER,MYSQL_PASSWORD=$MYSQL_PASSWORD,MYSQL_DB=$MYSQL_DB,MYSQL_PORT=$MYSQL_PORT}" \
        --region "$REGION"
else
    echo "🆕 Creating new Lambda function..."
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --role "$ROLE_ARN" \
        --handler "$HANDLER" \
        --zip-file "fileb://deploy/.build/${FUNCTION_NAME}.zip" \
        --timeout 30 \
        --memory-size 256 \
        --environment "Variables={MYSQL_HOST=$MYSQL_HOST,MYSQL_USER=$MYSQL_USER,MYSQL_PASSWORD=$MYSQL_PASSWORD,MYSQL_DB=$MYSQL_DB,MYSQL_PORT=$MYSQL_PORT}" \
        --region "$REGION"
fi

echo ""
echo "✅ Lambda function deployed successfully!"
echo ""
echo "=================================================="
echo "Next Steps:"
echo "=================================================="
echo "1. Add API Gateway integration:"
echo "   - Method: GET"
echo "   - Path: /customer/reviews-about-me"
echo "   - Authorization: Cognito User Pool"
echo ""
echo "2. Test the endpoint:"
echo "   curl -X GET \\"
echo "     'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me?limit=10' \\"
echo "     -H 'Authorization: Bearer \$TOKEN'"
echo ""
echo "=================================================="
