import json
import sys
import importlib.util

# Load the handler module
spec = importlib.util.spec_from_file_location(
    "handler", 
    "/Users/ykpfly/Desktop/capstone/quickfix_backend/lambda/bookings/get_booking_details/handler.py"
)
handler_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handler_module)
handler = handler_module.handler

test_event = {
    'requestContext': {
        'authorizer': {
            'jwt': {
                'claims': {
                    'sub': '917b35d0-9081-7071-db85-393f665485da'
                }
            }
        }
    },
    'pathParameters': {
        'booking_id': '75'
    }
}

print("🔍 Testing get_booking_details with booking_id=75 (has 3 images)")
print("=" * 70)

result = handler(test_event, None)
body = json.loads(result['body'])

print(f'\n✅ Status Code: {result["statusCode"]}')
print('\n📋 Booking Details:')
print(json.dumps(body['booking'], indent=2))

# Highlight the images
if body['booking']['images']:
    print(f"\n🖼️  Found {len(body['booking']['images'])} images:")
    for img in body['booking']['images']:
        print(f"   - Order {img['order']}: {img['url'][:80]}...")
else:
    print("\n⚠️  No images found")
