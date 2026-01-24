#!/bin/bash
# AWS SES Setup Script for QuickFix
# This script automates the SES configuration process

set -e

echo "🚀 QuickFix AWS SES Setup Script"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SES_REGION="us-east-1"
LAMBDA_REGION="us-east-2"

# Step 1: Get email address from user
echo -e "${YELLOW}Step 1: Email Verification${NC}"
read -p "Enter the email address you want to use as sender (e.g., your@email.com): " SENDER_EMAIL

if [ -z "$SENDER_EMAIL" ]; then
    echo -e "${RED}Error: Email address is required${NC}"
    exit 1
fi

# Step 2: Verify email in SES
echo ""
echo "Sending verification email to $SENDER_EMAIL..."
aws ses verify-email-identity \
    --email-address "$SENDER_EMAIL" \
    --region "$SES_REGION"

echo -e "${GREEN}✓${NC} Verification email sent!"
echo -e "${YELLOW}⚠️  Please check your inbox and click the verification link${NC}"
echo ""
read -p "Press Enter after you've clicked the verification link..."

# Step 3: Check verification status
echo ""
echo "Checking verification status..."
VERIFICATION_STATUS=$(aws ses get-identity-verification-attributes \
    --identities "$SENDER_EMAIL" \
    --region "$SES_REGION" \
    --query "VerificationAttributes.\"$SENDER_EMAIL\".VerificationStatus" \
    --output text)

if [ "$VERIFICATION_STATUS" == "Success" ]; then
    echo -e "${GREEN}✓${NC} Email verified successfully!"
else
    echo -e "${RED}✗${NC} Email not verified yet. Status: $VERIFICATION_STATUS"
    echo "Please wait a few minutes and try again."
    exit 1
fi

# Step 4: Check sandbox mode
echo ""
echo -e "${YELLOW}Step 2: Checking SES Account Status${NC}"
SANDBOX_STATUS=$(aws sesv2 get-account --region "$SES_REGION" --query "ProductionAccessEnabled" --output text 2>/dev/null || echo "false")

if [ "$SANDBOX_STATUS" == "false" ]; then
    echo -e "${YELLOW}⚠️  Your SES account is in SANDBOX mode${NC}"
    echo "   - You can only send emails TO verified addresses"
    echo "   - For testing, you'll need to verify recipient emails too"
    echo ""
    read -p "Do you want to verify a test recipient email? (y/n): " VERIFY_RECIPIENT
    
    if [ "$VERIFY_RECIPIENT" == "y" ]; then
        read -p "Enter test recipient email: " RECIPIENT_EMAIL
        aws ses verify-email-identity \
            --email-address "$RECIPIENT_EMAIL" \
            --region "$SES_REGION"
        echo -e "${GREEN}✓${NC} Verification email sent to $RECIPIENT_EMAIL"
        echo "   Please check that inbox and verify"
    fi
else
    echo -e "${GREEN}✓${NC} Your SES account is in PRODUCTION mode"
fi

# Step 5: Add SES permissions to Lambda roles
echo ""
echo -e "${YELLOW}Step 3: Adding SES Permissions to Lambda Roles${NC}"

# Create SES policy document
cat > /tmp/ses-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Add policy to create_booking role
ROLE_NAME="create_customer-role-qch33m23"
echo "Adding SES policy to $ROLE_NAME..."
aws iam put-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-name "SESEmailSendingPolicy" \
    --policy-document file:///tmp/ses-policy.json

echo -e "${GREEN}✓${NC} SES permissions added to create_booking Lambda role"

# Step 6: Update .env file
echo ""
echo -e "${YELLOW}Step 4: Updating .env File${NC}"

# Get frontend URL
read -p "Enter your frontend URL (or press Enter for placeholder): " FRONTEND_URL
if [ -z "$FRONTEND_URL" ]; then
    FRONTEND_URL="https://your-frontend-domain.com/provider/confirm-booking"
fi

# Check if .env already has SES config
if grep -q "SES_SENDER_EMAIL" .env; then
    echo "SES configuration already exists in .env"
    read -p "Do you want to update it? (y/n): " UPDATE_ENV
    if [ "$UPDATE_ENV" == "y" ]; then
        # Remove old SES config
        sed -i.bak '/SES_SENDER_EMAIL/d' .env
        sed -i.bak '/BOOKING_CONFIRMATION_URL/d' .env
        sed -i.bak '/AWS_SES_REGION/d' .env
    else
        echo "Skipping .env update"
        exit 0
    fi
fi

# Add SES configuration
cat >> .env << EOF

# ===========================
# AWS SES Configuration
# ===========================
SES_SENDER_EMAIL=$SENDER_EMAIL
BOOKING_CONFIRMATION_URL=$FRONTEND_URL
AWS_SES_REGION=$SES_REGION
EOF

echo -e "${GREEN}✓${NC} .env file updated"

# Step 7: Test SES
echo ""
echo -e "${YELLOW}Step 5: Testing SES${NC}"
read -p "Do you want to send a test email? (y/n): " SEND_TEST

if [ "$SEND_TEST" == "y" ]; then
    echo "Sending test email from $SENDER_EMAIL to $SENDER_EMAIL..."
    aws ses send-email \
        --from "$SENDER_EMAIL" \
        --to "$SENDER_EMAIL" \
        --subject "QuickFix SES Test" \
        --text "This is a test email from AWS SES. Your QuickFix booking confirmation workflow is ready!" \
        --region "$SES_REGION"
    
    echo -e "${GREEN}✓${NC} Test email sent! Check your inbox."
fi

# Cleanup
rm -f /tmp/ses-policy.json

echo ""
echo -e "${GREEN}=================================="
echo "✅ AWS SES Setup Complete!"
echo "==================================${NC}"
echo ""
echo "Configuration:"
echo "  - Sender Email: $SENDER_EMAIL"
echo "  - SES Region: $SES_REGION"
echo "  - Sandbox Mode: $([ "$SANDBOX_STATUS" == "false" ] && echo "Yes" || echo "No")"
echo ""
echo "Next Steps:"
echo "  → Phase 3: Create Email Service (src/email/ses_service.py)"
echo ""
