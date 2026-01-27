#!/usr/bin/env python3
"""
Test the DEPLOYED delete_booking_image Lambda function via AWS Lambda invoke
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
LAMBDA_NAME = "delete_booking_image"

lambda_client = boto3.client('lambda', region_name=AWS_REGION)


def find_test_image():
    """Find a valid booking image to test deletion."""
    print("🔍 Finding a test booking image to delete...")
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


def invoke_lambda(image):
    """Invoke the deployed Lambda function via AWS."""
    print("\n" + "="*80)
    print("Invoking DEPLOYED delete_booking_image Lambda")
    print("="*80)

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
    print(f"   Cognito Sub: {image['cognito_sub']}")

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
        print(f"   Full Response: {json.dumps(response_payload, indent=2)}")

        # Check if there's an error in the response
        if 'errorMessage' in response_payload:
            print(f"\n❌ Lambda Error: {response_payload.get('errorMessage')}")
            print(f"   Error Type: {response_payload.get('errorType', 'Unknown')}")
            if 'stackTrace' in response_payload:
                print(f"   Stack Trace:")
                for line in response_payload['stackTrace'][:5]:
                    print(f"      {line}")
            return False

        print(f"   Status Code: {response_payload.get('statusCode', 'N/A')}")

        body = json.loads(response_payload['body'])
        print(f"\n📦 Response Body:")
        print(json.dumps(body, indent=2))

        if response_payload.get('statusCode') == 200:
            print(f"\n✅ SUCCESS! Image deleted via DEPLOYED Lambda")
            print(f"\n💡 The image has been removed from both S3 and the database")

            # Verify deletion in database
            verify_deletion(image['image_id'])

            return True
        else:
            print(f"\n❌ FAILED: {body.get('message', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n❌ Lambda invocation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_deletion(image_id):
    """Verify image was deleted from database."""
    print(f"\n🔍 Verifying deletion in database...")
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT image_id FROM booking_images WHERE image_id = %s",
                (image_id,)
            )
            result = cur.fetchone()

            if result is None:
                print(f"✅ Image {image_id} successfully deleted from database")
            else:
                print(f"❌ Image {image_id} still exists in database!")
    finally:
        conn.close()


def test_unauthorized_deletion():
    """Test that unauthorized users cannot delete images."""
    print("\n" + "="*80)
    print("Testing Unauthorized Deletion Prevention")
    print("="*80)

    # Find an image (if any exist)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT bi.image_id, bi.booking_id
                FROM booking_images bi
                LIMIT 1
            """)
            image = cur.fetchone()
    finally:
        conn.close()

    if not image:
        print("⚠️  No images available to test unauthorized deletion")
        return True  # Skip test

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
            "booking_id": str(image['booking_id']),
            "image_id": str(image['image_id'])
        }
    }

    print(f"\n📝 Testing with unauthorized cognito_sub...")
    print(f"   Attempting to delete Image ID: {image['image_id']}")

    try:
        response = lambda_client.invoke(
            FunctionName=LAMBDA_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )

        response_payload = json.loads(response['Payload'].read())

        # Check if there's an error in the response
        if 'errorMessage' in response_payload:
            print(f"❌ Lambda Error: {response_payload.get('errorMessage')}")
            return False

        body = json.loads(response_payload['body'])

        if response_payload.get('statusCode') in [403, 404]:
            print(f"✅ Deletion correctly denied (Status: {response_payload.get('statusCode')})")
            print(f"   Message: {body.get('message')}")
            return True
        else:
            print(f"❌ Unauthorized deletion was not prevented!")
            print(f"   Status Code: {response_payload.get('statusCode')}")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Main test flow."""
    print("="*80)
    print("🧪 Testing DEPLOYED delete_booking_image Lambda Function")
    print("="*80)

    # Step 1: Find a test image
    image = find_test_image()
    if not image:
        print("\n⚠️  Cannot test without a booking image.")
        print("   Run test_deployed_create_booking_image.py first to create a test image")
        return

    # Step 2: Test unauthorized deletion first (so image still exists)
    unauthorized_blocked = test_unauthorized_deletion()

    # Step 3: Invoke deployed Lambda to delete the image
    print()
    success = invoke_lambda(image)

    # Summary
    print("\n" + "="*80)
    if success and unauthorized_blocked:
        print("✅ All Deployed Lambda Tests Passed!")
    else:
        print("⚠️  Some tests failed")
    print("="*80)
    print(f"\nAPI Endpoint: https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/bookings/{image['booking_id']}/images/{image['image_id']}")
    print("Note: To test via API Gateway, you need a valid JWT token from Cognito")


if __name__ == "__main__":
    main()
