"""
Test the deployed update_booking API endpoint
"""
import requests
import json
from datetime import datetime, timedelta

# API Configuration
API_BASE_URL = "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com"
BOOKING_ID = 82  # Using a testable booking in pending_confirmation status

# Get customer JWT token (you'll need to run get_customer_idtoken.py first)
# For now, we'll create a placeholder - you need to get the actual token
print("📝 To test the API, you need a valid JWT token.")
print("Run: python tests/get_customer_idtoken.py")
print("")
print("Then use the token in the test below:")
print("")

# Example test request (uncomment and add your token)
"""
JWT_TOKEN = "your-jwt-token-here"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

# Test 1: Reschedule booking
future_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
test_data = {
    "scheduled_date": future_date,
    "scheduled_time": "15:00:00",
    "notes": "Rescheduled via API test"
}

print(f"🧪 Testing API: PUT {API_BASE_URL}/customer/bookings/{BOOKING_ID}")
print(f"Request body: {json.dumps(test_data, indent=2)}")

response = requests.put(
    f"{API_BASE_URL}/customer/bookings/{BOOKING_ID}",
    headers=headers,
    json=test_data
)

print(f"\n📊 Response Status: {response.status_code}")
print(f"Response Body: {json.dumps(response.json(), indent=2)}")
"""

print("\n" + "="*60)
print("API Endpoint Information:")
print("="*60)
print(f"Base URL: {API_BASE_URL}")
print(f"Route: PUT /customer/bookings/{{booking_id}}")
print(f"Full URL: {API_BASE_URL}/customer/bookings/{{booking_id}}")
print(f"Authorization: Bearer <JWT_TOKEN>")
print("\nSupported Operations:")
print("  - Cancel: {\"status\": \"cancelled\"}")
print("  - Reschedule: {\"scheduled_date\": \"YYYY-MM-DD\", \"scheduled_time\": \"HH:MM:SS\"}")
print("  - Need more time: {\"status\": \"pending_reschedule\"}")
print("  - Update address: {\"service_address\": \"...\", \"service_city\": \"...\", ...}")
print("="*60)
