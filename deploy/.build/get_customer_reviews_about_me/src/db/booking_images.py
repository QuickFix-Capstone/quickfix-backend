"""
Utility functions for booking_images table operations.
"""
from botocore.exceptions import ClientError

try:
    from .rds_main import get_connection
except ImportError:
    from rds_main import get_connection


def get_booking_images_count(conn, booking_id):
    """
    Get count of images for a booking.

    Args:
        conn: Database connection
        booking_id: Booking ID

    Returns:
        int: Number of images for this booking
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) as count FROM booking_images WHERE booking_id = %s",
            (booking_id,)
        )
        result = cur.fetchone()
        return result['count'] if result else 0


def verify_booking_ownership(conn, booking_id, customer_id):
    """
    Verify customer owns booking.

    Args:
        conn: Database connection
        booking_id: Booking ID
        customer_id: Customer ID

    Returns:
        bool: True if customer owns booking, False otherwise
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT booking_id FROM bookings WHERE booking_id = %s AND customer_id = %s",
            (booking_id, customer_id)
        )
        return cur.fetchone() is not None


def verify_booking_access(conn, booking_id, customer_id=None, provider_id=None):
    """
    Verify user has access to booking (either as customer or provider).

    Args:
        conn: Database connection
        booking_id: Booking ID
        customer_id: Customer ID (optional)
        provider_id: Provider ID (optional)

    Returns:
        bool: True if user has access, False otherwise
    """
    with conn.cursor() as cur:
        if customer_id:
            cur.execute(
                "SELECT booking_id FROM bookings WHERE booking_id = %s AND customer_id = %s",
                (booking_id, customer_id)
            )
            return cur.fetchone() is not None
        elif provider_id:
            cur.execute(
                "SELECT booking_id FROM bookings WHERE booking_id = %s AND provider_id = %s",
                (booking_id, provider_id)
            )
            return cur.fetchone() is not None
    return False


def get_used_image_orders(conn, booking_id):
    """
    Get list of used image_order values for a booking.

    Args:
        conn: Database connection
        booking_id: Booking ID

    Returns:
        list: List of used image_order values (1-5)
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT image_order FROM booking_images WHERE booking_id = %s",
            (booking_id,)
        )
        return [row['image_order'] for row in cur.fetchall()]


def is_image_order_available(conn, booking_id, image_order):
    """
    Check if image_order is available for a booking.

    Args:
        conn: Database connection
        booking_id: Booking ID
        image_order: Image order (1-5)

    Returns:
        bool: True if available, False if already used
    """
    used_orders = get_used_image_orders(conn, booking_id)
    return image_order not in used_orders


def get_booking_image_by_id(conn, image_id):
    """
    Get booking image by image_id.

    Args:
        conn: Database connection
        image_id: Image ID

    Returns:
        dict or None: Image record if found
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT image_id, booking_id, image_key, image_order, content_type,
                   file_size, description, uploaded_by_id, created_at, updated_at
            FROM booking_images
            WHERE image_id = %s
            """,
            (image_id,)
        )
        return cur.fetchone()


def get_booking_images(conn, booking_id):
    """
    Get all images for a booking, ordered by image_order.

    Args:
        conn: Database connection
        booking_id: Booking ID

    Returns:
        list: List of image records
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT image_id, booking_id, image_key, image_order, content_type,
                   file_size, description, uploaded_by_id, created_at, updated_at
            FROM booking_images
            WHERE booking_id = %s
            ORDER BY image_order ASC
            """,
            (booking_id,)
        )
        return cur.fetchall()


def create_booking_image(conn, booking_id, image_key, image_order, content_type,
                         file_size, uploaded_by_id, description=None):
    """
    Create a new booking image record.

    Args:
        conn: Database connection
        booking_id: Booking ID
        image_key: S3 key
        image_order: Display order (1-5)
        content_type: MIME type
        file_size: File size in bytes
        uploaded_by_id: Customer ID who uploaded
        description: Optional description

    Returns:
        dict: {'success': bool, 'image_id': int} or {'success': False, 'error': str}
    """
    try:
        with conn.cursor() as cur:
            sql = """
                INSERT INTO booking_images
                (booking_id, image_key, image_order, content_type, file_size,
                 uploaded_by_id, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql, (
                booking_id, image_key, image_order, content_type,
                file_size, uploaded_by_id, description
            ))
            conn.commit()
            return {
                "success": True,
                "image_id": cur.lastrowid
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def delete_booking_image(conn, image_id):
    """
    Delete a booking image record.

    Args:
        conn: Database connection
        image_id: Image ID

    Returns:
        dict: {'success': bool} or {'success': False, 'error': str}
    """
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM booking_images WHERE image_id = %s", (image_id,))
            conn.commit()
            return {"success": True}
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def verify_s3_object_exists(s3_client, bucket, key):
    """
    Check if S3 object exists.

    Args:
        s3_client: boto3 S3 client
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        bool: True if object exists, False otherwise
    """
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError:
        return False


# Test code
if __name__ == "__main__":
    print("---- Testing booking_images utilities ----")

    conn = get_connection()

    try:
        # Test get_booking_images_count
        print("\nTest 1: get_booking_images_count")
        count = get_booking_images_count(conn, 1)
        print(f"✅ Image count for booking 1: {count}")

        # Test verify_booking_ownership
        print("\nTest 2: verify_booking_ownership")
        owns = verify_booking_ownership(conn, 1, 1)
        print(f"✅ Customer 1 owns booking 1: {owns}")

        # Test get_used_image_orders
        print("\nTest 3: get_used_image_orders")
        used_orders = get_used_image_orders(conn, 1)
        print(f"✅ Used image orders for booking 1: {used_orders}")

        # Test is_image_order_available
        print("\nTest 4: is_image_order_available")
        available = is_image_order_available(conn, 1, 1)
        print(f"✅ Image order 1 available for booking 1: {available}")

        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")

    finally:
        conn.close()
