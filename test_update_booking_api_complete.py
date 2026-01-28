"""
Complete API test for update_booking endpoint
Gets JWT token and tests the deployed API
"""
import boto3
import requests
import json
from datetime import datetime, timedelta

# Cognito Configuration
USER_POOL_ID = "us-east-2_45z5OMePi"
CLIENT_ID = "p2u5qdegml3hp60n6ohu52n2b"
AWS_REGION = "us-east-2"

# Customer credentials
EMAIL = "ykphrfly@gmail.com"
PASSWORD = "Yang@860101"

# API Configuration
API_BASE_URL = "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com"
BOOKING_ID = 82  # pending_confirmation status

print("🔐 Getting JWT token for customer...")
print(f"Email: {EMAIL}")

# Get JWT token
client = boto3.client('cognito-idp', region_name=AWS_REGION)

try:
    response = client.initiate_auth(
        ClientId=CLIENT_ID,
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': EMAIL,
            'PASSWORD': PASSWORD
        }
    )
    
    jwt_token = response['AuthenticationResult']['IdToken']
    print("✅ JWT token obtained successfully")
    print(f"Token (first 50 chars): {jwt_token[:50]}...")
    
except Exception as e:
    print(f"❌ Failed to get JWT token: {e}")
    exit(1)

# Test API
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}

print("\n" + "="*70)
print("🧪 Testing Update Booking API")
print("="*70)

# Test 1: Cancel booking (should work for pending_confirmation)
print(f"\n📋 Test 1: Cancel Booking #{BOOKING_ID}")
test_data_1 = {
    "status": "cancelled",
    "notes": "Cancelled via deployed API test"
}

print(f"URL: PUT {API_BASE_URL}/customer/bookings/{BOOKING_ID}")
print(f"Body: {json.dumps(test_data_1, indent=2)}")

response_1 = requests.put(
    f"{API_BASE_URL}/customer/bookings/{BOOKING_ID}",
    headers=headers,
    json=test_data_1
)

print(f"\n📊 Response Status: {response_1.status_code}")
if response_1.status_code == 200:
    print("✅ SUCCESS")
    result = response_1.json()
    if 'booking' in result:
        booking = result['booking']
        print(f"   Status: {booking['status']}")
        print(f"   Notes: {booking.get('notes', 'N/A')}")
else:
    print(f"❌ FAILED")
    print(f"Response: {json.dumps(response_1.json(), indent=2)}")

# Test 2: Try to reschedule (should fail - booking is now cancelled or was pending_confirmation)
print(f"\n📋 Test 2: Try to Reschedule (Expected to Fail)")
future_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
test_data_2 = {
    "scheduled_date": future_date,
    "scheduled_time": "15:00:00",
    "notes": "Attempting to reschedule"
}

print(f"Body: {json.dumps(test_data_2, indent=2)}")

response_2 = requests.put(
    f"{API_BASE_URL}/customer/bookings/{BOOKING_ID}",
    headers=headers,
    json=test_data_2
)

print(f"\n📊 Response Status: {response_2.status_code}")
if response_2.status_code == 200:
    print("✅ SUCCESS")
    result = response_2.json()
    if 'booking' in result:
        booking = result['booking']
        print(f"   New Status: {booking['status']}")
        print(f"   Notes: {booking.get('notes', 'N/A')}")
else:
    print(f"Response: {json.dumps(response_2.json(), indent=2)}")

# Test 3: Try to reschedule to past date (should fail)
print(f"\n📋 Test 3: Try Rescheduling to Past Date (Should Fail)")
past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
test_data_3 = {
    "scheduled_date": past_date,
    "scheduled_time": "10:00:00"
}

print(f"Body: {json.dumps(test_data_3, indent=2)}")

response_3 = requests.put(
    f"{API_BASE_URL}/customer/bookings/{BOOKING_ID}",
    headers=headers,
    json=test_data_3
)

print(f"\n📊 Response Status: {response_3.status_code}")
if response_3.status_code == 400:
    print("✅ CORRECTLY REJECTED")
    print(f"   Error: {response_3.json().get('message', 'N/A')}")
else:
    print(f"❌ Should have been rejected!")
    print(f"Response: {json.dumps(response_3.json(), indent=2)}")

print("\n" + "="*70)
print("✅ API Testing Complete!")
print("="*70)
