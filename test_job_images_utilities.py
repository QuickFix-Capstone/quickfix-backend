#!/usr/bin/env python3
"""
Comprehensive test script for job_images utility functions.

This script will:
1. Find or create a test job
2. Test all job_images utility functions
3. Create, read, and delete test image records
4. Verify all operations work correctly
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.db.rds_main import get_connection
from src.db.job_images import (
    get_job_images_count,
    verify_job_ownership,
    get_used_image_orders,
    is_image_order_available,
    get_job_image_by_id,
    get_job_images,
    create_job_image,
    delete_job_image
)


def find_or_create_test_job(conn):
    """Find an existing job or create a test job for testing."""
    with conn.cursor() as cur:
        # Try to find an existing job
        cur.execute("SELECT job_id, customer_id FROM jobs LIMIT 1")
        job = cur.fetchone()
        
        if job:
            print(f"✅ Found existing job: job_id={job['job_id']}, customer_id={job['customer_id']}")
            return job['job_id'], job['customer_id']
        
        # If no jobs exist, create a test job
        print("⚠️  No existing jobs found. Creating test job...")
        
        # Get a customer to use
        cur.execute("SELECT customer_id FROM customers LIMIT 1")
        customer = cur.fetchone()
        
        if not customer:
            print("❌ No customers found in database. Cannot create test job.")
            return None, None
        
        customer_id = customer['customer_id']
        
        # Create test job
        cur.execute("""
            INSERT INTO jobs (customer_id, title, description, location_address)
            VALUES (%s, %s, %s, %s)
        """, (customer_id, "Test Job for Image Testing", "Test description", "123 Test St"))
        conn.commit()
        
        job_id = cur.lastrowid
        print(f"✅ Created test job: job_id={job_id}, customer_id={customer_id}")
        return job_id, customer_id


def test_job_images_utilities():
    """Run comprehensive tests on job_images utilities."""
    
    print("=" * 80)
    print("🧪 TESTING JOB_IMAGES UTILITY FUNCTIONS")
    print("=" * 80)
    
    conn = get_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    test_image_ids = []  # Track created images for cleanup
    
    try:
        # Setup: Find or create test job
        print("\n📋 SETUP: Finding test job...")
        job_id, customer_id = find_or_create_test_job(conn)
        
        if not job_id or not customer_id:
            print("❌ Failed to get test job")
            return False
        
        print(f"\n🎯 Using job_id={job_id}, customer_id={customer_id} for tests\n")
        
        # Test 1: get_job_images_count (should be 0 initially)
        print("-" * 80)
        print("TEST 1: get_job_images_count()")
        count = get_job_images_count(conn, job_id)
        print(f"  Initial image count for job {job_id}: {count}")
        initial_count = count
        print("  ✅ PASSED")
        
        # Test 2: verify_job_ownership (should be True)
        print("-" * 80)
        print("TEST 2: verify_job_ownership()")
        owns = verify_job_ownership(conn, job_id, customer_id)
        print(f"  Customer {customer_id} owns job {job_id}: {owns}")
        assert owns == True, "Customer should own the job"
        print("  ✅ PASSED")
        
        # Test 3: verify_job_ownership with wrong customer (should be False)
        print("-" * 80)
        print("TEST 3: verify_job_ownership() with wrong customer")
        wrong_customer_id = customer_id + 9999
        owns_wrong = verify_job_ownership(conn, job_id, wrong_customer_id)
        print(f"  Customer {wrong_customer_id} owns job {job_id}: {owns_wrong}")
        assert owns_wrong == False, "Wrong customer should not own the job"
        print("  ✅ PASSED")
        
        # Test 4: get_used_image_orders (should be empty initially)
        print("-" * 80)
        print("TEST 4: get_used_image_orders()")
        used_orders = get_used_image_orders(conn, job_id)
        print(f"  Used image orders for job {job_id}: {used_orders}")
        print("  ✅ PASSED")
        
        # Test 5: is_image_order_available (all should be available)
        print("-" * 80)
        print("TEST 5: is_image_order_available()")
        for order in range(1, 6):
            available = is_image_order_available(conn, job_id, order)
            print(f"  Image order {order} available: {available}")
            assert available == True, f"Order {order} should be available"
        print("  ✅ PASSED")
        
        # Test 6: create_job_image (create test image)
        print("-" * 80)
        print("TEST 6: create_job_image()")
        result = create_job_image(
            conn=conn,
            job_id=job_id,
            image_key=f"job-images/{job_id}/test-image-1.jpg",
            image_order=1,
            content_type="image/jpeg",
            file_size=1024000,
            uploaded_by_id=customer_id,
            description="Test image 1"
        )
        print(f"  Create result: {result}")
        assert result['success'] == True, "Image creation should succeed"
        image_id_1 = result['image_id']
        test_image_ids.append(image_id_1)
        print(f"  Created image with ID: {image_id_1}")
        print("  ✅ PASSED")
        
        # Test 7: get_job_images_count (should be 1 now)
        print("-" * 80)
        print("TEST 7: get_job_images_count() after creating image")
        count = get_job_images_count(conn, job_id)
        print(f"  Image count for job {job_id}: {count}")
        assert count == initial_count + 1, f"Count should be {initial_count + 1}"
        print("  ✅ PASSED")
        
        # Test 8: get_job_image_by_id
        print("-" * 80)
        print("TEST 8: get_job_image_by_id()")
        image = get_job_image_by_id(conn, image_id_1)
        print(f"  Retrieved image: {image}")
        assert image is not None, "Image should be found"
        assert image['job_id'] == job_id, "Job ID should match"
        assert image['image_order'] == 1, "Image order should be 1"
        print("  ✅ PASSED")
        
        # Test 9: Create second image
        print("-" * 80)
        print("TEST 9: create_job_image() - second image")
        result2 = create_job_image(
            conn=conn,
            job_id=job_id,
            image_key=f"job-images/{job_id}/test-image-2.jpg",
            image_order=2,
            content_type="image/jpeg",
            file_size=2048000,
            uploaded_by_id=customer_id,
            description="Test image 2"
        )
        assert result2['success'] == True, "Second image creation should succeed"
        image_id_2 = result2['image_id']
        test_image_ids.append(image_id_2)
        print(f"  Created second image with ID: {image_id_2}")
        print("  ✅ PASSED")
        
        # Test 10: get_job_images (should return 2 images)
        print("-" * 80)
        print("TEST 10: get_job_images()")
        images = get_job_images(conn, job_id)
        print(f"  Retrieved {len(images)} images:")
        for img in images:
            print(f"    - Image {img['image_id']}: order={img['image_order']}, key={img['image_key']}")
        assert len(images) >= 2, "Should have at least 2 images"
        print("  ✅ PASSED")
        
        # Test 11: get_used_image_orders (should show 1 and 2)
        print("-" * 80)
        print("TEST 11: get_used_image_orders() after creating images")
        used_orders = get_used_image_orders(conn, job_id)
        print(f"  Used image orders: {used_orders}")
        assert 1 in used_orders, "Order 1 should be used"
        assert 2 in used_orders, "Order 2 should be used"
        print("  ✅ PASSED")
        
        # Test 12: is_image_order_available (1 and 2 should be unavailable)
        print("-" * 80)
        print("TEST 12: is_image_order_available() after creating images")
        available_1 = is_image_order_available(conn, job_id, 1)
        available_2 = is_image_order_available(conn, job_id, 2)
        available_3 = is_image_order_available(conn, job_id, 3)
        print(f"  Order 1 available: {available_1} (should be False)")
        print(f"  Order 2 available: {available_2} (should be False)")
        print(f"  Order 3 available: {available_3} (should be True)")
        assert available_1 == False, "Order 1 should not be available"
        assert available_2 == False, "Order 2 should not be available"
        assert available_3 == True, "Order 3 should be available"
        print("  ✅ PASSED")
        
        # Test 13: Try to create duplicate image_order (should fail)
        print("-" * 80)
        print("TEST 13: create_job_image() with duplicate image_order (should fail)")
        result_dup = create_job_image(
            conn=conn,
            job_id=job_id,
            image_key=f"job-images/{job_id}/test-image-duplicate.jpg",
            image_order=1,  # Duplicate order
            content_type="image/jpeg",
            file_size=1024000,
            uploaded_by_id=customer_id
        )
        print(f"  Create result: {result_dup}")
        assert result_dup['success'] == False, "Duplicate order should fail"
        print(f"  Expected failure: {result_dup.get('error', 'Unknown error')}")
        print("  ✅ PASSED")
        
        # Test 14: delete_job_image
        print("-" * 80)
        print("TEST 14: delete_job_image()")
        delete_result = delete_job_image(conn, image_id_1)
        print(f"  Delete result: {delete_result}")
        assert delete_result['success'] == True, "Delete should succeed"
        test_image_ids.remove(image_id_1)  # Remove from cleanup list
        print("  ✅ PASSED")
        
        # Test 15: Verify deletion
        print("-" * 80)
        print("TEST 15: Verify image was deleted")
        deleted_image = get_job_image_by_id(conn, image_id_1)
        print(f"  Deleted image lookup: {deleted_image}")
        assert deleted_image is None, "Deleted image should not be found"
        count_after_delete = get_job_images_count(conn, job_id)
        print(f"  Image count after delete: {count_after_delete}")
        print("  ✅ PASSED")
        
        # Cleanup: Delete remaining test images
        print("\n" + "=" * 80)
        print("🧹 CLEANUP: Deleting remaining test images...")
        for img_id in test_image_ids:
            delete_job_image(conn, img_id)
            print(f"  Deleted image {img_id}")
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Final cleanup
        try:
            for img_id in test_image_ids:
                delete_job_image(conn, img_id)
        except:
            pass
        conn.close()


if __name__ == "__main__":
    success = test_job_images_utilities()
    sys.exit(0 if success else 1)
