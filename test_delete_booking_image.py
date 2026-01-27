#!/usr/bin/env python3
"""
Test delete_booking_image Lambda function
"""
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.db.rds_main import get_connection

def find_test_image():
    """Find a valid booking image to test with."""
    print("🔍 Finding a test booking image...")
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            # Get a booking image with customer and booking info
            cur.execute("""
                SELECT
                    bi.image_id,
                    bi.booking_id,
                    bi.image_key,
                    bi.image_order,
                    b.customer_id,
                    c.cognito_sub,
                    c.first_name,
                    c.last_name
                FROM booking_images bi
                JOIN bookings b ON bi.booking_id = b.booking_id
                JOIN customers c ON b.customer_id = c.customer_id
                LIMIT 1
            """)
            image = cur.fetchone()

            if image:
                print(f"✅ Found test image:")
                print(f"   Image ID: {image['image_id']}")
                print(f"   Booking ID: {image['booking_id']}")
                print(f"   Image Key: {image['image_key']}")
                print(f"   Image Order: {image['image_order']}")
                print(f"   Customer: {image['first_name']} {image['last_name']}")
                print(f"   Cognito Sub: {image['cognito_sub']}")
                return image
            else:
                print("❌ No booking images found in database")
                return None
    finally:
        conn.close()

def test_handler():
    """Test the delete_booking_image handler."""

    # Find a test image
    image = find_test_image()
    if not image:
        print("\n⚠️  Cannot test without a booking image. Upload an image first.")
        return

    print("\n" + "="*80)
    print("Testing delete_booking_image Lambda Handler")
    print("="*80)

    # Add lambda directory to path
    lambda_path = os.path.join(os.path.dirname(__file__), 'lambda', 'bookings', 'delete_booking_image')
    sys.path.insert(0, lambda_path)

    # Import handler
    import handler as delete_handler

    # Create test event
    test_event = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": image['cognito_sub']
                    }
                }
            }
        },
        "pathParameters": {
            "booking_id": str(image['booking_id']),
            "image_id": str(image['image_id'])
        }
    }

    print(f"\n📝 Test Input:")
    print(f"   Booking ID: {image['booking_id']}")
    print(f"   Image ID: {image['image_id']}")
    print(f"   Image Key: {image['image_key']}")

    print(f"\n🚀 Calling handler...")
    result = delete_handler.handler(test_event, None)

    print(f"\n📊 Response:")
    print(f"   Status Code: {result['statusCode']}")

    body = json.loads(result['body'])
    print(f"\n📦 Response Body:")
    print(json.dumps(body, indent=2))

    if result['statusCode'] == 200:
        print(f"\n✅ SUCCESS! Image deleted")
        print(f"\n💡 The image has been removed from both S3 and the database")
    else:
        print(f"\n❌ FAILED: {body.get('message', 'Unknown error')}")

if __name__ == "__main__":
    test_handler()
