#!/usr/bin/env bash
# Test the deployed create_booking API with confirmation workflow

# Get API endpoint
API_URL="https://zzh7jdvhq1.execute-api.us-east-2.amazonaws.com/prod/bookings"

# Get fresh customer token
echo "🔐 Getting fresh customer JWT token..."
./get_customer_token.sh > /dev/null 2>&1

# Load token from file
CUSTOMER_TOKEN=$(cat /tmp/customer_jwt_token.txt)

if [ -z "$CUSTOMER_TOKEN" ]; then
    echo "❌ Failed to get customer token"
    exit 1
fi

echo "✅ Customer token obtained"
echo ""

# Create test booking
echo "📋 Creating test booking..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

RESPONSE=$(curl -s -X POST "$API_URL" \
  -H "Authorization: Bearer $CUSTOMER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_id": "SP-001",
    "service_category": "plumber",
    "service_description": "Fix leaking kitchen sink - LIVE API TEST",
    "scheduled_date": "2026-02-01",
    "scheduled_time": "15:00",
    "service_address": "456 API Test Street",
    "service_city": "Boston",
    "service_state": "MA",
    "service_postal_code": "02101",
    "estimated_price": 175.00,
    "notes": "Testing deployed Lambda with confirmation workflow"
  }')

echo "📤 API Response:"
echo "$RESPONSE" | jq '.'
echo ""

# Parse response
STATUS=$(echo "$RESPONSE" | jq -r '.booking.status // "error"')
BOOKING_ID=$(echo "$RESPONSE" | jq -r '.booking.booking_id // "N/A"')

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$STATUS" = "pending_confirmation" ]; then
    echo "✅ SUCCESS! Booking created with confirmation workflow"
    echo ""
    echo "📋 Booking Details:"
    echo "   Booking ID: $BOOKING_ID"
    echo "   Status: $STATUS"
    echo ""
    echo "🔍 Next Steps:"
    echo "   1. Check database for confirmation_token"
    echo "   2. Check CloudWatch logs for email sending status"
    echo "   3. Verify NO job was created yet"
    echo ""
    echo "📧 Expected Email:"
    echo "   To: john.carter@quickfix.dev (if verified in SES)"
    echo "   Subject: New Booking Request #$BOOKING_ID - QuickFix"
    echo ""
else
    echo "❌ FAILED or unexpected status: $STATUS"
    echo "   Booking ID: $BOOKING_ID"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
