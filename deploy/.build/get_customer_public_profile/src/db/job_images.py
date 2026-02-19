"""
Utility functions for job_images table operations.
"""
from botocore.exceptions import ClientError

try:
    from .rds_main import get_connection
except ImportError:
    from rds_main import get_connection


def get_job_images_count(conn, job_id):
    """
    Get count of images for a job.

    Args:
        conn: Database connection
        job_id: Job ID

    Returns:
        int: Number of images for this job
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) as count FROM job_images WHERE job_id = %s",
            (job_id,)
        )
        result = cur.fetchone()
        return result['count'] if result else 0


def verify_job_ownership(conn, job_id, customer_id):
    """
    Verify customer owns job.

    Args:
        conn: Database connection
        job_id: Job ID
        customer_id: Customer ID

    Returns:
        bool: True if customer owns job, False otherwise
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT job_id FROM jobs WHERE job_id = %s AND customer_id = %s",
            (job_id, customer_id)
        )
        return cur.fetchone() is not None


def get_used_image_orders(conn, job_id):
    """
    Get list of used image_order values for a job.

    Args:
        conn: Database connection
        job_id: Job ID

    Returns:
        list: List of used image_order values (1-5)
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT image_order FROM job_images WHERE job_id = %s",
            (job_id,)
        )
        return [row['image_order'] for row in cur.fetchall()]


def is_image_order_available(conn, job_id, image_order):
    """
    Check if image_order is available for a job.

    Args:
        conn: Database connection
        job_id: Job ID
        image_order: Image order (1-5)

    Returns:
        bool: True if available, False if already used
    """
    used_orders = get_used_image_orders(conn, job_id)
    return image_order not in used_orders


def get_job_image_by_id(conn, image_id):
    """
    Get job image by image_id.

    Args:
        conn: Database connection
        image_id: Image ID

    Returns:
        dict or None: Image record if found
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT image_id, job_id, image_key, image_order, content_type,
                   file_size, description, uploaded_by_id, created_at, updated_at
            FROM job_images
            WHERE image_id = %s
            """,
            (image_id,)
        )
        return cur.fetchone()


def get_job_images(conn, job_id):
    """
    Get all images for a job, ordered by image_order.

    Args:
        conn: Database connection
        job_id: Job ID

    Returns:
        list: List of image records
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT image_id, job_id, image_key, image_order, content_type,
                   file_size, description, uploaded_by_id, created_at, updated_at
            FROM job_images
            WHERE job_id = %s
            ORDER BY image_order ASC
            """,
            (job_id,)
        )
        return cur.fetchall()


def create_job_image(conn, job_id, image_key, image_order, content_type,
                     file_size, uploaded_by_id, description=None):
    """
    Create a new job image record.

    Args:
        conn: Database connection
        job_id: Job ID
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
                INSERT INTO job_images
                (job_id, image_key, image_order, content_type, file_size,
                 uploaded_by_id, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql, (
                job_id, image_key, image_order, content_type,
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


def delete_job_image(conn, image_id):
    """
    Delete a job image record.

    Args:
        conn: Database connection
        image_id: Image ID

    Returns:
        dict: {'success': bool} or {'success': False, 'error': str}
    """
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM job_images WHERE image_id = %s", (image_id,))
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
    print("---- Testing job_images utilities ----")

    conn = get_connection()

    try:
        # Test get_job_images_count
        print("\nTest 1: get_job_images_count")
        count = get_job_images_count(conn, 1)
        print(f"✅ Image count for job 1: {count}")

        # Test verify_job_ownership
        print("\nTest 2: verify_job_ownership")
        owns = verify_job_ownership(conn, 1, 1)
        print(f"✅ Customer 1 owns job 1: {owns}")

        # Test get_used_image_orders
        print("\nTest 3: get_used_image_orders")
        used_orders = get_used_image_orders(conn, 1)
        print(f"✅ Used image orders for job 1: {used_orders}")

        # Test is_image_order_available
        print("\nTest 4: is_image_order_available")
        available = is_image_order_available(conn, 1, 1)
        print(f"✅ Image order 1 available for job 1: {available}")

        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")

    finally:
        conn.close()
