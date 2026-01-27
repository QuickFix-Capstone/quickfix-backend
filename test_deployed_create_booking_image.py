#!/usr/bin/env python3
"""
Test the DEPLOYED create_booking_image Lambda function via AWS Lambda invoke
"""
import sys
import os
import json
import boto3
from datetime import datetime
from io import BytesIO
from PIL import Image

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.db.rds_main import get_connection

# AWS Configuration
AWS_REGION = "us-east-2"
LAMBDA_NAME = "create_booking_image"
S3_BUCKET = "quickfix-app-files"

lambda_client = boto3.client('lambda', region_name=AWS_REGION)
s3_client = boto3.client('s3', region_name=AWS_REGION)


def find_test_booking():
    """Find a valid booking to test with."""
    print("🔍 Finding a test booking...")
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            # Get booking 75
            cur.execute("""
                SELECT b.booking_id, b.customer_id, c.cognito_sub, c.first_name, c.last_name
                FROM bookings b
                JOIN customers c ON b.customer_id = c.customer_id
                WHERE b.booking_id = 75
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
                print("❌ No booking found")
                return None
    finally:
        conn.close()


def find_available_image_order(booking_id):
    """Find an available image_order slot for the booking."""
    print(f"\n🔍 Finding available image_order for booking {booking_id}...")
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT image_order FROM booking_images WHERE booking_id = %s",
                (booking_id,)
            )
            used_orders = [row['image_order'] for row in cur.fetchall()]

            print(f"   Used orders: {used_orders}")

            # Find first available order (1-5)
            for order in range(1, 6):
                if order not in used_orders:
                    print(f"✅ Available image_order: {order}")
                    return order

            print("❌ All image orders (1-5) are already used")
            return None
    finally:
        conn.close()


def create_dummy_image():
    """Create a simple test image in memory."""
    print("\n🖼️  Creating dummy test image...")

    # Create a 800x600 image with a colored background
    img = Image.new('RGB', (800, 600), color='#E94E77')  # Different color for deployed test

    # Convert to bytes
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG', quality=85)
    img_bytes.seek(0)

    file_size = img_bytes.getbuffer().nbytes
    print(f"✅ Created dummy image: {file_size} bytes")

    return img_bytes, file_size


def upload_to_s3(booking_id, image_bytes):
    """Upload image to S3 and return the S3 key."""
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    s3_key = f"booking-images/{booking_id}/{timestamp}-deployed-test.jpg"

    print(f"\n☁️  Uploading to S3...")
    print(f"   Bucket: {S3_BUCKET}")
    print(f"   Key: {s3_key}")

    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=image_bytes,
            ContentType='image/jpeg'
        )
        print(f"✅ Upload successful!")
        return s3_key
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None


def invoke_lambda(booking, image_order, s3_key, file_size):
    """Invoke the deployed Lambda function via AWS."""
    print("\n" + "="*80)
    print("Invoking DEPLOYED create_booking_image Lambda")
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
        },
        "body": json.dumps({
            "image_key": s3_key,
            "image_order": image_order,
            "content_type": "image/jpeg",
            "file_size": file_size,
            "description": "Deployed Lambda test image"
        })
    }

    print(f"\n📝 Test Input:")
    print(f"   Booking ID: {booking['booking_id']}")
    print(f"   Image Key: {s3_key}")
    print(f"   Image Order: {image_order}")
    print(f"   Content Type: image/jpeg")
    print(f"   File Size: {file_size} bytes")

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
            print(f"\n✅ SUCCESS! Image metadata saved via DEPLOYED Lambda")
            print(f"\n🔑 Key details:")
            print(f"   Image ID: {body.get('image_id', 'N/A')}")
            print(f"   Booking ID: {body.get('booking_id', 'N/A')}")
            print(f"   Image Order: {body.get('image_order', 'N/A')}")
            return True
        else:
            print(f"\n❌ FAILED: {body.get('message', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n❌ Lambda invocation failed: {e}")
        return False


def verify_database_record(booking_id, image_order):
    """Verify the record was saved in the database."""
    print("\n" + "="*80)
    print("Verifying Database Record")
    print("="*80)

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT image_id, booking_id, image_key, image_order, content_type,
                       file_size, description, uploaded_by_id, created_at
                FROM booking_images
                WHERE booking_id = %s AND image_order = %s
            """, (booking_id, image_order))

            record = cur.fetchone()

            if record:
                print(f"\n✅ Record found in database:")
                print(f"   Image ID: {record['image_id']}")
                print(f"   Booking ID: {record['booking_id']}")
                print(f"   Image Key: {record['image_key']}")
                print(f"   Image Order: {record['image_order']}")
                print(f"   Content Type: {record['content_type']}")
                print(f"   File Size: {record['file_size']} bytes")
                print(f"   Description: {record['description']}")
                print(f"   Uploaded By: {record['uploaded_by_id']}")
                print(f"   Created At: {record['created_at']}")
                return True
            else:
                print(f"\n❌ No record found for booking {booking_id}, order {image_order}")
                return False
    finally:
        conn.close()


def main():
    """Main test flow."""
    print("="*80)
    print("🧪 Testing DEPLOYED create_booking_image Lambda Function")
    print("="*80)

    # Step 1: Find a test booking
    booking = find_test_booking()
    if not booking:
        print("\n⚠️  Cannot test without a booking.")
        return

    # Step 2: Find available image_order
    image_order = find_available_image_order(booking['booking_id'])
    if image_order is None:
        print("\n⚠️  All image orders are used. Delete some images first.")
        return

    # Step 3: Create dummy image
    image_bytes, file_size = create_dummy_image()

    # Step 4: Upload to S3
    s3_key = upload_to_s3(booking['booking_id'], image_bytes)
    if not s3_key:
        print("\n⚠️  Failed to upload image to S3. Cannot proceed with test.")
        return

    # Step 5: Invoke deployed Lambda
    success = invoke_lambda(booking, image_order, s3_key, file_size)

    if success:
        # Step 6: Verify database record
        verify_database_record(booking['booking_id'], image_order)

        print("\n" + "="*80)
        print("✅ Deployed Lambda Test Complete!")
        print("="*80)
        print(f"\nAPI Endpoint: https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/bookings/{booking['booking_id']}/images")
        print("Note: To test via API Gateway, you need a valid JWT token from Cognito")
    else:
        print("\n" + "="*80)
        print("❌ Deployed Lambda Test Failed")
        print("="*80)


if __name__ == "__main__":
    main()
