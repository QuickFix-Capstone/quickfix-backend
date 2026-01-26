#!/usr/bin/env python3
"""
Test create_booking_image Lambda function
This test:
1. Finds a test booking
2. Creates a dummy image file
3. Uploads it to S3
4. Calls the create_booking_image handler to save metadata
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

# S3 Configuration
S3_BUCKET = os.environ.get('S3_BUCKET', 'quickfix-app-files')
s3_client = boto3.client('s3')


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
                WHERE b.booking_id = 75
                LIMIT 1
            """)
            booking = cur.fetchone()

            if not booking:
                # Try any booking if 75 doesn't exist
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
    img = Image.new('RGB', (800, 600), color='#4A90E2')

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
    s3_key = f"booking-images/{booking_id}/{timestamp}-test-image.jpg"

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


def test_handler(booking, image_order, s3_key, file_size):
    """Test the create_booking_image handler."""

    print("\n" + "="*80)
    print("Testing create_booking_image Lambda Handler")
    print("="*80)

    # Add lambda directory to path
    lambda_path = os.path.join(os.path.dirname(__file__), 'lambda', 'bookings', 'create_booking_image')
    sys.path.insert(0, lambda_path)

    # Import handler
    import handler as create_handler

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
            "description": "Test image for booking"
        })
    }

    print(f"\n📝 Test Input:")
    print(f"   Booking ID: {booking['booking_id']}")
    print(f"   Image Key: {s3_key}")
    print(f"   Image Order: {image_order}")
    print(f"   Content Type: image/jpeg")
    print(f"   File Size: {file_size} bytes")

    print(f"\n🚀 Calling handler...")
    result = create_handler.handler(test_event, None)

    print(f"\n📊 Response:")
    print(f"   Status Code: {result['statusCode']}")

    body = json.loads(result['body'])
    print(f"\n📦 Response Body:")
    print(json.dumps(body, indent=2))

    if result['statusCode'] == 200:
        print(f"\n✅ SUCCESS! Image metadata saved to database")
        print(f"\n🔑 Key details:")
        print(f"   Image ID: {body.get('image_id', 'N/A')}")
        print(f"   Booking ID: {body.get('booking_id', 'N/A')}")
        print(f"   Image Order: {body.get('image_order', 'N/A')}")
    else:
        print(f"\n❌ FAILED: {body.get('message', 'Unknown error')}")


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
            else:
                print(f"\n❌ No record found for booking {booking_id}, order {image_order}")
    finally:
        conn.close()


def main():
    """Main test flow."""
    print("="*80)
    print("🧪 Testing create_booking_image Lambda Function")
    print("="*80)

    # Step 1: Find a test booking
    booking = find_test_booking()
    if not booking:
        print("\n⚠️  Cannot test without a booking. Create a booking first.")
        return

    # Step 2: Find available image_order
    image_order = find_available_image_order(booking['booking_id'])
    if image_order is None:
        print("\n⚠️  All image orders are used. Delete some images first or use a different booking.")
        return

    # Step 3: Create dummy image
    image_bytes, file_size = create_dummy_image()

    # Step 4: Upload to S3
    s3_key = upload_to_s3(booking['booking_id'], image_bytes)
    if not s3_key:
        print("\n⚠️  Failed to upload image to S3. Cannot proceed with test.")
        return

    # Step 5: Test the handler
    test_handler(booking, image_order, s3_key, file_size)

    # Step 6: Verify database record
    verify_database_record(booking['booking_id'], image_order)

    print("\n" + "="*80)
    print("✅ Test Complete!")
    print("="*80)


if __name__ == "__main__":
    main()
