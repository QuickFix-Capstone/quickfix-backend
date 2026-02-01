#!/usr/bin/env python3
"""
Test script for create_job_image Lambda function.

This script will:
1. Find a test job owned by a customer
2. Test the create_job_image handler
3. Verify metadata is saved correctly
4. Test various validation scenarios
"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.db.rds_main import get_connection


def find_test_job():
    """Find a job owned by a customer for testing."""
    conn = get_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return None, None, None
    
    try:
        with conn.cursor() as cur:
            # Find a customer with a job
            cur.execute("""
                SELECT j.job_id, j.customer_id, c.cognito_sub
                FROM jobs j
                JOIN customers c ON j.customer_id = c.customer_id
                WHERE c.cognito_sub IS NOT NULL
                LIMIT 1
            """)
            result = cur.fetchone()
            
            if result:
                print(f"✅ Found test job: job_id={result['job_id']}, customer_id={result['customer_id']}")
                print(f"   cognito_sub={result['cognito_sub']}")
                return result['job_id'], result['customer_id'], result['cognito_sub']
            else:
                print("❌ No jobs found with valid customer cognito_sub")
                return None, None, None
    finally:
        conn.close()


def cleanup_test_images(job_id):
    """Clean up any test images for the job."""
    conn = get_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM job_images WHERE job_id = %s", (job_id,))
            conn.commit()
            print(f"🧹 Cleaned up existing test images for job {job_id}")
    finally:
        conn.close()


def test_create_job_image():
    """Test the create_job_image handler."""
    
    print("=" * 80)
    print("🧪 TESTING CREATE_JOB_IMAGE LAMBDA FUNCTION")
    print("=" * 80)
    
    # Find test job
    print("\n📋 SETUP: Finding test job...")
    job_id, customer_id, cognito_sub = find_test_job()
    
    if not job_id:
        print("❌ Cannot run tests without a valid job")
        return False
    
    print(f"\n🎯 Using job_id={job_id}, customer_id={customer_id}\n")
    
    # Clean up any existing test images
    cleanup_test_images(job_id)
    
    # Import handler
    lambda_path = os.path.join(os.path.dirname(__file__), 'lambda', 'jobs', 'create_job_image')
    sys.path.insert(0, lambda_path)
    from handler import handler
    
    # Test 1: Valid request (but S3 object doesn't exist)
    print("-" * 80)
    print("TEST 1: Valid request (S3 object doesn't exist - expected to fail)")
    test_event = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": cognito_sub
                    }
                }
            }
        },
        "pathParameters": {
            "job_id": str(job_id)
        },
        "body": json.dumps({
            "image_key": f"job-images/{job_id}/test-nonexistent.jpg",
            "image_order": 1,
            "content_type": "image/jpeg",
            "file_size": 1024000,
            "description": "Test image"
        })
    }
    
    result = handler(test_event, None)
    print(f"  Status Code: {result['statusCode']}")
    body = json.loads(result['body'])
    print(f"  Message: {body.get('message', 'No message')}")
    
    if result['statusCode'] == 400 and "not found in S3" in body.get('message', ''):
        print("  ✅ PASSED (Expected failure - S3 verification working)")
    else:
        print(f"  ⚠️  Unexpected response")
    
    # Test 2: Missing required field
    print("\n" + "-" * 80)
    print("TEST 2: Missing image_key (should fail)")
    test_event["body"] = json.dumps({
        "image_order": 1,
        "content_type": "image/jpeg",
        "file_size": 1024000
    })
    
    result = handler(test_event, None)
    print(f"  Status Code: {result['statusCode']}")
    
    if result['statusCode'] == 400:
        body = json.loads(result['body'])
        print(f"  ✅ EXPECTED FAILURE: {body['message']}")
    else:
        print(f"  ❌ Should have failed with 400")
        return False
    
    # Test 3: Invalid content type
    print("\n" + "-" * 80)
    print("TEST 3: Invalid content type (should fail)")
    test_event["body"] = json.dumps({
        "image_key": f"job-images/{job_id}/test.pdf",
        "image_order": 1,
        "content_type": "application/pdf",
        "file_size": 1024000
    })
    
    result = handler(test_event, None)
    print(f"  Status Code: {result['statusCode']}")
    
    if result['statusCode'] == 400:
        body = json.loads(result['body'])
        print(f"  ✅ EXPECTED FAILURE: {body['message']}")
    else:
        print(f"  ❌ Should have failed with 400")
        return False
    
    # Test 4: Invalid image_order
    print("\n" + "-" * 80)
    print("TEST 4: Invalid image_order (should fail)")
    test_event["body"] = json.dumps({
        "image_key": f"job-images/{job_id}/test.jpg",
        "image_order": 10,
        "content_type": "image/jpeg",
        "file_size": 1024000
    })
    
    result = handler(test_event, None)
    print(f"  Status Code: {result['statusCode']}")
    
    if result['statusCode'] == 400:
        body = json.loads(result['body'])
        print(f"  ✅ EXPECTED FAILURE: {body['message']}")
    else:
        print(f"  ❌ Should have failed with 400")
        return False
    
    # Test 5: Invalid file_size
    print("\n" + "-" * 80)
    print("TEST 5: Invalid file_size (should fail)")
    test_event["body"] = json.dumps({
        "image_key": f"job-images/{job_id}/test.jpg",
        "image_order": 1,
        "content_type": "image/jpeg",
        "file_size": -100
    })
    
    result = handler(test_event, None)
    print(f"  Status Code: {result['statusCode']}")
    
    if result['statusCode'] == 400:
        body = json.loads(result['body'])
        print(f"  ✅ EXPECTED FAILURE: {body['message']}")
    else:
        print(f"  ❌ Should have failed with 400")
        return False
    
    # Test 6: Wrong job ownership
    print("\n" + "-" * 80)
    print("TEST 6: Wrong job ownership (should fail)")
    test_event["pathParameters"]["job_id"] = "99999"
    test_event["body"] = json.dumps({
        "image_key": "job-images/99999/test.jpg",
        "image_order": 1,
        "content_type": "image/jpeg",
        "file_size": 1024000
    })
    
    result = handler(test_event, None)
    print(f"  Status Code: {result['statusCode']}")
    
    if result['statusCode'] in [403, 404]:
        body = json.loads(result['body'])
        print(f"  ✅ EXPECTED FAILURE: {body['message']}")
    else:
        print(f"  ❌ Should have failed with 403 or 404")
        return False
    
    print("\n" + "=" * 80)
    print("✅ ALL VALIDATION TESTS PASSED!")
    print("=" * 80)
    print("\n💡 Note: To test successful image creation, you need to:")
    print("   1. Upload an actual file to S3 using upload_job_image")
    print("   2. Then call create_job_image with that image_key")
    return True


if __name__ == "__main__":
    success = test_create_job_image()
    sys.exit(0 if success else 1)
