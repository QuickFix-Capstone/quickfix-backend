#!/usr/bin/env python3
"""
Test get_booking_images Lambda function
This test:
1. Finds a test booking with images
2. Calls the get_booking_images handler to retrieve all images
3. Verifies response format and presigned URLs
"""
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.db.rds_main import get_connection


def find_test_booking_with_images():
    """Find a booking that has images."""
    print("🔍 Finding a test booking with images...")
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            # Get booking 75 (which we've been testing with)
            cur.execute("""
                SELECT b.booking_id, b.customer_id, c.cognito_sub, c.first_name, c.last_name,
                       COUNT(bi.image_id) as image_count
                FROM bookings b
                JOIN customers c ON b.customer_id = c.customer_id
                LEFT JOIN booking_images bi ON b.booking_id = bi.booking_id
                WHERE b.booking_id = 75
                GROUP BY b.booking_id, b.customer_id, c.cognito_sub, c.first_name, c.last_name
            """)
            booking = cur.fetchone()

            if booking:
                print(f"✅ Found test booking:")
                print(f"   Booking ID: {booking['booking_id']}")
                print(f"   Customer: {booking['first_name']} {booking['last_name']}")
                print(f"   Cognito Sub: {booking['cognito_sub']}")
                print(f"   Image Count: {booking['image_count']}")
                return booking
            else:
                print("❌ Booking 75 not found")
                return None
    finally:
        conn.close()


def check_booking_images(booking_id):
    """Check existing images for the booking."""
    print(f"\n📷 Checking existing images for booking {booking_id}...")
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT image_id, image_key, image_order, content_type,
                       file_size, description, created_at
                FROM booking_images
                WHERE booking_id = %s
                ORDER BY image_order
            """, (booking_id,))
            images = cur.fetchall()

            if images:
                print(f"✅ Found {len(images)} images:")
                for img in images:
                    print(f"   - Image #{img['image_order']}: {img['image_key']}")
                    print(f"     Size: {img['file_size']} bytes, Type: {img['content_type']}")
                return images
            else:
                print("⚠️  No images found for this booking")
                print("\n💡 To test this endpoint, you need to:")
                print("   1. Run test_create_booking_image.py to create some test images first")
                print("   2. Then run this test again")
                return []
    finally:
        conn.close()


def test_handler(booking):
    """Test the get_booking_images handler."""

    print("\n" + "="*80)
    print("Testing get_booking_images Lambda Handler")
    print("="*80)

    # Add lambda directory to path
    lambda_path = os.path.join(os.path.dirname(__file__), 'lambda', 'bookings', 'get_booking_images')
    sys.path.insert(0, lambda_path)

    # Import handler
    import handler as get_handler

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
        }
    }

    print(f"\n📝 Test Input:")
    print(f"   Booking ID: {booking['booking_id']}")
    print(f"   Cognito Sub: {booking['cognito_sub']}")

    print(f"\n🚀 Calling handler...")
    result = get_handler.handler(test_event, None)

    print(f"\n📊 Response:")
    print(f"   Status Code: {result['statusCode']}")

    body = json.loads(result['body'])
    print(f"\n📦 Response Body:")
    print(json.dumps(body, indent=2))

    if result['statusCode'] == 200:
        print(f"\n✅ SUCCESS! Retrieved {body['count']} images")

        if body['count'] > 0:
            print(f"\n🖼️  Image Details:")
            for i, image in enumerate(body['images'], 1):
                print(f"\n   Image {i}:")
                print(f"      Image ID: {image['image_id']}")
                print(f"      Order: {image['image_order']}")
                print(f"      S3 Key: {image['image_key']}")
                print(f"      Content Type: {image['content_type']}")
                print(f"      File Size: {image['file_size']} bytes")
                print(f"      Description: {image.get('description', 'N/A')}")
                print(f"      Uploaded By: {image['uploaded_by_id']}")
                print(f"      Created At: {image['created_at']}")
                print(f"      Presigned URL: {image['url'][:80]}..." if image.get('url') else "      URL: None")

            # Validate presigned URLs
            print(f"\n🔐 Presigned URL Validation:")
            all_urls_valid = True
            for image in body['images']:
                if image.get('url') and image['url'].startswith('https://'):
                    print(f"   ✅ Image {image['image_order']}: Valid presigned URL")
                else:
                    print(f"   ❌ Image {image['image_order']}: Invalid or missing URL")
                    all_urls_valid = False

            if all_urls_valid:
                print(f"\n✅ All presigned URLs are valid!")
        else:
            print(f"\n⚠️  No images found for this booking")
            print(f"   Run test_create_booking_image.py to add test images first")

        return True
    else:
        print(f"\n❌ FAILED: {body.get('message', 'Unknown error')}")
        return False


def test_unauthorized_access():
    """Test that unauthorized users cannot access booking images."""
    print("\n" + "="*80)
    print("Testing Unauthorized Access Prevention")
    print("="*80)

    # Add lambda directory to path
    lambda_path = os.path.join(os.path.dirname(__file__), 'lambda', 'bookings', 'get_booking_images')
    sys.path.insert(0, lambda_path)

    # Import handler
    import handler as get_handler

    # Use a different cognito_sub (not the owner)
    test_event = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "00000000-0000-0000-0000-000000000000"  # Fake user
                    }
                }
            }
        },
        "pathParameters": {
            "booking_id": "75"
        }
    }

    print(f"\n📝 Testing with unauthorized cognito_sub...")
    result = get_handler.handler(test_event, None)

    body = json.loads(result['body'])

    if result['statusCode'] in [403, 404]:
        print(f"✅ Access correctly denied (Status: {result['statusCode']})")
        print(f"   Message: {body.get('message')}")
        return True
    else:
        print(f"❌ Unauthorized access was not prevented!")
        print(f"   Status Code: {result['statusCode']}")
        return False


def main():
    """Main test flow."""
    print("="*80)
    print("🧪 Testing get_booking_images Lambda Function")
    print("="*80)

    # Step 1: Find a test booking
    booking = find_test_booking_with_images()
    if not booking:
        print("\n⚠️  Cannot test without a booking. Create a booking first.")
        return

    # Step 2: Check existing images
    images = check_booking_images(booking['booking_id'])

    # Step 3: Test the handler
    success = test_handler(booking)

    # Step 4: Test unauthorized access
    print()
    unauthorized_blocked = test_unauthorized_access()

    # Summary
    print("\n" + "="*80)
    if success and unauthorized_blocked:
        print("✅ All Tests Passed!")
    else:
        print("⚠️  Some tests failed")
    print("="*80)

    if booking['image_count'] == 0:
        print("\n💡 Tip: Run test_create_booking_image.py to add test images")
        print("   Then run this test again to see image retrieval in action")


if __name__ == "__main__":
    main()
