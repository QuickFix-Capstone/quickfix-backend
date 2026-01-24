#!/bin/bash
# Manual SES Setup - Individual Commands
# Use these if you prefer to run commands one by one

# ============================================
# 1. VERIFY YOUR EMAIL
# ============================================
# Replace with your email address
EMAIL="your-email@example.com"

aws ses verify-email-identity \
  --email-address "$EMAIL" \
  --region us-east-1

echo "✓ Verification email sent to $EMAIL"
echo "→ Check your inbox and click the verification link"
echo ""

# ============================================
# 2. CHECK VERIFICATION STATUS
# ============================================
# Wait a few minutes, then run:
aws ses get-identity-verification-attributes \
  --identities "$EMAIL" \
  --region us-east-1

# Look for "VerificationStatus": "Success"

# ============================================
# 3. ADD SES PERMISSIONS TO LAMBDA ROLE
# ============================================
# Create policy file
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

# Add to Lambda role
aws iam put-role-policy \
  --role-name "create_customer-role-qch33m23" \
  --policy-name "SESEmailSendingPolicy" \
  --policy-document file:///tmp/ses-policy.json

echo "✓ SES permissions added to Lambda role"

# ============================================
# 4. TEST SES
# ============================================
aws ses send-email \
  --from "$EMAIL" \
  --to "$EMAIL" \
  --subject "QuickFix SES Test" \
  --text "This is a test email from AWS SES" \
  --region us-east-1

echo "✓ Test email sent!"
