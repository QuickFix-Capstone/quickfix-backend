#!/usr/bin/env python3
"""
Test script for create_booking Lambda handler with confirmation workflow
"""

import json
import sys
import os
import importlib.util

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

# Import handler using importlib to avoid 'lambda' keyword issue
spec = importlib.util.spec_from_file_location("handler", "lambda/bookings/create_booking/handler.py")
handler_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handler_module)
handler = handler_module.handler

# Test event with mock JWT claims
test_event = {
    "requestContext": {
        "authorizer": {
            "jwt": {
                "claims": {
                    # Real customer cognito_sub from database (Customer 1 - ajaypersaudyt@gmail.com)
                    "sub": "819bd5f0-e011-7081-2819-5188d5a2bb2f"
                }
            }
        }
    },
    "body": json.dumps({
        # Use a real provider_id from database (SP-001 - John Carter)
        "provider_id": "SP-001",
        "service_category": "plumber",
        "service_description": "Fix leaking kitchen sink - TEST BOOKING",
        "scheduled_date": "2026-01-30",  # Future date
        "scheduled_time": "14:00",
        "service_address": "123 Test Street",
        "service_city": "Boston",
        "service_state": "MA",
        "service_postal_code": "02101",
        "estimated_price": 150.00,
        "notes": "This is a test booking for confirmation workflow"
    })
}

print("=" * 80)
print("🧪 TESTING create_booking Lambda Handler")
print("=" * 80)
print()
print("📋 Test Configuration:")
print(f"   Customer: 819bd5f0-e011-7081-2819-5188d5a2bb2f (ajaypersaudyt@gmail.com)")
print(f"   Provider: SP-001 (John Carter - john.carter@quickfix.dev)")
print(f"   Service: Plumber - Fix leaking kitchen sink")
print(f"   Date: 2026-01-30 at 14:00")
print()
print("=" * 80)
print("🚀 Running handler...")
print("=" * 80)
print()

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
        print(f"📋 Booking Created:")
        print(f"   Booking ID: {booking.get('booking_id')}")
        print(f"   Status: {booking.get('status')}")
        print(f"   Service: {booking.get('service_category')}")
        print(f"   Date: {booking.get('scheduled_date')} at {booking.get('scheduled_time')}")
        print()
        
        print("🔍 What to check:")
        print("   1. Check your email (ykphrfly@gmail.com) for confirmation email")
        print("   2. Check database for booking record with status='pending_confirmation'")
        print("   3. Verify confirmation_token is set in database")
        print("   4. Verify NO job was created yet (jobs table should be empty for this booking)")
        print()
        
        print("📧 Expected Email:")
        print("   To: john.carter@quickfix.dev")
        print("   Subject: New Booking Request #[ID] - QuickFix")
        print("   Content: Confirmation link with token")
        print()
        
    else:
        print(f"❌ Status: FAILED ({status_code})")
        print(f"   Message: {body.get('message')}")
        print()
        
        if 'missing' in body:
            print(f"   Missing fields: {body.get('missing')}")
    
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
