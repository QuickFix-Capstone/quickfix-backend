#!/usr/bin/env python3
"""
Test email sending by creating a new booking
This will trigger the email notification to the service provider
"""

import json
import sys
import os
import importlib.util
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

# Import handler using importlib
spec = importlib.util.spec_from_file_location("handler", "lambda/bookings/create_booking/handler.py")
handler_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handler_module)
handler = handler_module.handler

print("=" * 80)
print("🧪 TESTING EMAIL DELIVERY - Create Booking")
print("=" * 80)
print()

# Use the verified provider: yang test (ykphrfly@gmail.com)
PROVIDER_ID = "SP-36954b19-d60f-431b-866f-cd6859828b90"
CUSTOMER_COGNITO_SUB = "819bd5f0-e011-7081-2819-5188d5a2bb2f"  # From previous tests

# Calculate future date
future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

print("📋 Test Configuration:")
print(f"   Provider: yang test (ykphrfly@gmail.com) ✅ VERIFIED")
print(f"   Provider ID: {PROVIDER_ID}")
print(f"   Customer Cognito Sub: {CUSTOMER_COGNITO_SUB}")
print(f"   Scheduled Date: {future_date}")
print()
print("=" * 80)
print("🚀 Creating booking...")
print("=" * 80)
print()

# Create test event
test_event = {
    "requestContext": {
        "authorizer": {
            "jwt": {
                "claims": {
                    "sub": CUSTOMER_COGNITO_SUB
                }
            }
        }
    },
    "body": json.dumps({
        "provider_id": PROVIDER_ID,
        "service_category": "plumber",
        "service_description": "EMAIL TEST - Fix leaking bathroom sink",
        "scheduled_date": future_date,
        "scheduled_time": "15:00",
        "service_address": "456 Test Avenue",
        "service_city": "Boston",
        "service_state": "MA",
        "service_postal_code": "02101",
        "estimated_price": 175.00,
        "notes": "This is a test booking to verify email delivery"
    })
}

try:
    result = handler(test_event, None)
    
    print("=" * 80)
    print("📤 RESPONSE:")
    print("=" * 80)
    print(json.dumps(result, indent=2))
    print()
    
    # Parse response
    status_code = result.get('statusCode')
    body = json.loads(result.get('body', '{}'))
    
    print("=" * 80)
    print("✅ TEST RESULTS:")
    print("=" * 80)
    
    if status_code == 201:
        print("✅ Status: SUCCESS (201)")
        print()
        
        booking = body.get('booking', {})
        booking_id = booking.get('booking_id')
        status = booking.get('status')
        
        print(f"📋 Booking Created:")
        print(f"   Booking ID: {booking_id}")
        print(f"   Status: {status}")
        print(f"   Provider: {booking.get('provider_name')}")
        print(f"   Service: {booking.get('service_category')}")
        print(f"   Date: {booking.get('scheduled_date')} at {booking.get('scheduled_time')}")
        print()
        
        print("📧 EMAIL VERIFICATION:")
        print("   ✅ Email should be sent to: ykphrfly@gmail.com")
        print("   ✅ Subject: New Booking Request #{} - QuickFix".format(booking_id))
        print()
        print("🔍 CHECK YOUR EMAIL INBOX NOW!")
        print("   1. Open ykphrfly@gmail.com")
        print("   2. Look for email from: ykphrfly@gmail.com")
        print("   3. Subject: 'New Booking Request #{} - QuickFix'".format(booking_id))
        print("   4. Check spam folder if not in inbox")
        print()
        print("📧 Email should contain:")
        print("   - Customer name")
        print("   - Service description: 'EMAIL TEST - Fix leaking bathroom sink'")
        print("   - Scheduled date & time")
        print("   - Service address: 456 Test Avenue")
        print("   - 'Confirm Booking' button")
        print()
        
    else:
        print(f"❌ Status: FAILED ({status_code})")
        print(f"   Message: {body.get('message')}")
        print()
    
    print("=" * 80)
    
except Exception as e:
    print("=" * 80)
    print("❌ ERROR:")
    print("=" * 80)
    print(f"   {type(e).__name__}: {str(e)}")
    print()
    import traceback
    traceback.print_exc()
    print("=" * 80)
