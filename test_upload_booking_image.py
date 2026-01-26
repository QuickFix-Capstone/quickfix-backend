#!/usr/bin/env python3
"""
Test upload_booking_image Lambda function
"""
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.db.rds_main import get_connection

def find_test_booking():
    """Find a valid booking to test with."""
    print("🔍 Finding a test booking...")
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            # Get a booking with its customer info
            cur.execute("""
                SELECT b.booking_id, b.customer_id, c.cognito_sub, c.first_name, c.last_name
                FROM bookings b
                JOIN customers c ON b.customer_id = c.customer_id
                LIMIT 1
            """)
            booking = cur.fetchone()

            if booking:
                print(f"✅ Found test booking:")
                print(f"   Booking ID: {booking['booking_id']}")
                print(f"   Customer: {booking['first_name']} {booking['last_name']}")
                print(f"   Cognito Sub: {booking['cognito_sub']}")
                return booking
            else:
                print("❌ No bookings found in database")
                return None
    finally:
        conn.close()

def test_handler():
    """Test the upload_booking_image handler."""

    # Find a test booking
    booking = find_test_booking()
    if not booking:
        print("\n⚠️  Cannot test without a booking. Create a booking first.")
        return

    print("\n" + "="*80)
    print("Testing upload_booking_image Lambda Handler")
    print("="*80)

    # Add lambda directory to path
    lambda_path = os.path.join(os.path.dirname(__file__), 'lambda', 'bookings', 'upload_booking_image')
    sys.path.insert(0, lambda_path)

    # Import handler
    import handler as upload_handler

    # Create test event
    test_event = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": booking['cognito_sub']
                    }
                }
            }
        },
        "pathParameters": {
            "booking_id": str(booking['booking_id'])
        },
        "body": json.dumps({
            "file_name": "kitchen_leak.jpg",
            "content_type": "image/jpeg",
            "image_order": 1
        })
    }

    print(f"\n📝 Test Input:")
    print(f"   Booking ID: {booking['booking_id']}")
    print(f"   File Name: kitchen_leak.jpg")
    print(f"   Content Type: image/jpeg")
    print(f"   Image Order: 1")

    print(f"\n🚀 Calling handler...")
    result = upload_handler.handler(test_event, None)

    print(f"\n📊 Response:")
    print(f"   Status Code: {result['statusCode']}")

    body = json.loads(result['body'])
    print(f"\n📦 Response Body:")
    print(json.dumps(body, indent=2))

    if result['statusCode'] == 200:
        print(f"\n✅ SUCCESS! Presigned URL generated")
        print(f"\n🔑 Key details:")
        print(f"   Upload URL: {body.get('upload_url', 'N/A')}")
        print(f"   Image Key: {body.get('image_key', 'N/A')}")
        print(f"   Expires In: {body.get('expires_in', 'N/A')} seconds")
        print(f"\n💡 Next step: Use this presigned URL to upload the image to S3")
    else:
        print(f"\n❌ FAILED: {body.get('message', 'Unknown error')}")

if __name__ == "__main__":
    test_handler()
