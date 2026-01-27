#!/usr/bin/env python3
"""
Test the DEPLOYED get_booking_images Lambda function via AWS Lambda invoke
"""
import sys
import os
import json
import boto3

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.db.rds_main import get_connection

# AWS Configuration
AWS_REGION = "us-east-2"
LAMBDA_NAME = "get_booking_images"

lambda_client = boto3.client('lambda', region_name=AWS_REGION)


def find_test_booking():
    """Find a test booking with images."""
    print("🔍 Finding a test booking with images...")
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            # Get booking 75 with image count
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


def invoke_lambda(booking):
    """Invoke the deployed Lambda function via AWS."""
    print("\n" + "="*80)
    print("Invoking DEPLOYED get_booking_images Lambda")
    print("="*80)

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

    print(f"\n🚀 Invoking Lambda: {LAMBDA_NAME}...")

    try:
        response = lambda_client.invoke(
            FunctionName=LAMBDA_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )

        # Read response
        response_payload = json.loads(response['Payload'].read())

        print(f"\n📊 Lambda Response:")
        print(f"   Status Code: {response_payload.get('statusCode', 'N/A')}")

        body = json.loads(response_payload['body'])
        print(f"\n📦 Response Body:")
        print(json.dumps(body, indent=2))

        if response_payload.get('statusCode') == 200:
            print(f"\n✅ SUCCESS! Retrieved {body['count']} images via DEPLOYED Lambda")

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
                    print(f"      Presigned URL: {image['url'][:80]}..." if image.get('url') else "      URL: None")

                # Validate presigned URLs
                print(f"\n🔐 Presigned URL Validation:")
                all_valid = True
                for image in body['images']:
                    if image.get('url') and image['url'].startswith('https://'):
                        print(f"   ✅ Image {image['image_order']}: Valid presigned URL")
                    else:
                        print(f"   ❌ Image {image['image_order']}: Invalid or missing URL")
                        all_valid = False

                if all_valid:
                    print(f"\n✅ All presigned URLs are valid!")

            return True
        else:
            print(f"\n❌ FAILED: {body.get('message', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n❌ Lambda invocation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unauthorized_access():
    """Test that unauthorized users cannot access booking images."""
    print("\n" + "="*80)
    print("Testing Unauthorized Access Prevention")
    print("="*80)

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

    try:
        response = lambda_client.invoke(
            FunctionName=LAMBDA_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )

        response_payload = json.loads(response['Payload'].read())
        body = json.loads(response_payload['body'])

        if response_payload.get('statusCode') in [403, 404]:
            print(f"✅ Access correctly denied (Status: {response_payload.get('statusCode')})")
            print(f"   Message: {body.get('message')}")
            return True
        else:
            print(f"❌ Unauthorized access was not prevented!")
            print(f"   Status Code: {response_payload.get('statusCode')}")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Main test flow."""
    print("="*80)
    print("🧪 Testing DEPLOYED get_booking_images Lambda Function")
    print("="*80)

    # Step 1: Find a test booking
    booking = find_test_booking()
    if not booking:
        print("\n⚠️  Cannot test without a booking.")
        return

    if booking['image_count'] == 0:
        print("\n⚠️  No images found for this booking.")
        print("   Run test_create_booking_image.py or test_deployed_create_booking_image.py first")
        print("   to add some test images, then run this test again.")
        return

    # Step 2: Invoke deployed Lambda
    success = invoke_lambda(booking)

    # Step 3: Test unauthorized access
    print()
    unauthorized_blocked = test_unauthorized_access()

    # Summary
    print("\n" + "="*80)
    if success and unauthorized_blocked:
        print("✅ All Deployed Lambda Tests Passed!")
    else:
        print("⚠️  Some tests failed")
    print("="*80)
    print(f"\nAPI Endpoint: https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/bookings/{booking['booking_id']}/images")
    print("Note: To test via API Gateway, you need a valid JWT token from Cognito")


if __name__ == "__main__":
    main()
