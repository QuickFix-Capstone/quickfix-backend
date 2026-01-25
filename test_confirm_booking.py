#!/usr/bin/env python3
"""
Test script for confirm_booking Lambda handler
Tests the complete confirmation workflow with a real token
"""

import json
import sys
import os
import importlib.util

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

# Import handler using importlib
spec = importlib.util.spec_from_file_location("handler", "lambda/bookings/confirm_booking/handler.py")
handler_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handler_module)
handler = handler_module.handler

# Real token from booking ID 35
TOKEN = "0e9de52815b3c09784bb0cf2404e78fdb0dbc0c75a7b3ffb983cbee04b317d8d"

print("=" * 80)
print("🧪 TESTING confirm_booking Lambda Handler")
print("=" * 80)
print()
print("📋 Test Configuration:")
print(f"   Booking ID: 35")
print(f"   Token: {TOKEN[:32]}...")
print(f"   Expected Status: pending_confirmation → confirmed")
print()
print("=" * 80)
print("🚀 Running handler...")
print("=" * 80)
print()

# Test event simulating API Gateway
test_event = {
    "queryStringParameters": {
        "token": TOKEN
    }
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
    
    if status_code == 200:
        print("✅ Status: SUCCESS (200)")
        print()
        
        booking_id = body.get('booking_id')
        job_id = body.get('job_id')
        status = body.get('status')
        
        print(f"📋 Confirmation Details:")
        print(f"   Booking ID: {booking_id}")
        print(f"   Job ID: {job_id}")
        print(f"   New Status: {status}")
        print()
        
        print("🔍 What to verify:")
        print("   1. Check database: booking status = 'confirmed'")
        print("   2. Check database: job exists with job_id = {job_id}")
        print("   3. Check database: booking.job_id and job.booking_id are linked")
        print("   4. Check email sent to customer (if email configured)")
        print()
        
        print("📧 Expected Email:")
        print("   To: ajaypersaudyt@gmail.com")
        print("   Subject: Booking Confirmed #35 - QuickFix")
        print("   Content: Job details and confirmation")
        print()
        
    elif status_code == 409:
        print("⚠️  Status: ALREADY CONFIRMED (409)")
        print(f"   Message: {body.get('message')}")
        print()
        print("   This is expected if you run the test twice!")
        print("   The booking can only be confirmed once.")
        print()
        
    else:
        print(f"❌ Status: FAILED ({status_code})")
        print(f"   Message: {body.get('message')}")
        print(f"   Error Code: {body.get('error_code')}")
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
