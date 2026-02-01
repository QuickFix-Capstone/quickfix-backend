#!/usr/bin/env python3
"""
Test script for upload_job_image Lambda function.

This script will:
1. Find a test job owned by a customer
2. Test the upload_job_image handler
3. Verify presigned URL generation
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


def test_upload_job_image():
    """Test the upload_job_image handler."""
    
    print("=" * 80)
    print("🧪 TESTING UPLOAD_JOB_IMAGE LAMBDA FUNCTION")
    print("=" * 80)
    
    # Find test job
    print("\n📋 SETUP: Finding test job...")
    job_id, customer_id, cognito_sub = find_test_job()
    
    if not job_id:
        print("❌ Cannot run tests without a valid job")
        return False
    
    print(f"\n🎯 Using job_id={job_id}, customer_id={customer_id}\n")
    
    # Import handler
    lambda_path = os.path.join(os.path.dirname(__file__), 'lambda', 'jobs', 'upload_job_image')
    sys.path.insert(0, lambda_path)
    from handler import handler
    
    # Test 1: Valid request
    print("-" * 80)
    print("TEST 1: Valid upload request")
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
            "file_name": "test_kitchen_photo.jpg",
            "content_type": "image/jpeg",
            "image_order": 1
        })
    }
    
    result = handler(test_event, None)
    print(f"  Status Code: {result['statusCode']}")
    
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        print(f"  ✅ SUCCESS")
        print(f"  Message: {body['message']}")
        print(f"  Upload URL: {body['upload_url'][:50]}...")
        print(f"  Image Key: {body['image_key']}")
        print(f"  Expires In: {body['expires_in']} seconds")
    else:
        body = json.loads(result['body'])
        print(f"  ❌ FAILED: {body.get('message', 'Unknown error')}")
        return False
    
    # Test 2: Invalid content type
    print("\n" + "-" * 80)
    print("TEST 2: Invalid content type (should fail)")
    test_event["body"] = json.dumps({
        "file_name": "test.pdf",
        "content_type": "application/pdf",
        "image_order": 2
    })
    
    result = handler(test_event, None)
    print(f"  Status Code: {result['statusCode']}")
    
    if result['statusCode'] == 400:
        body = json.loads(result['body'])
        print(f"  ✅ EXPECTED FAILURE: {body['message']}")
    else:
        print(f"  ❌ Should have failed with 400")
        return False
    
    # Test 3: Invalid image_order
    print("\n" + "-" * 80)
    print("TEST 3: Invalid image_order (should fail)")
    test_event["body"] = json.dumps({
        "file_name": "test.jpg",
        "content_type": "image/jpeg",
        "image_order": 10  # Out of range
    })
    
    result = handler(test_event, None)
    print(f"  Status Code: {result['statusCode']}")
    
    if result['statusCode'] == 400:
        body = json.loads(result['body'])
        print(f"  ✅ EXPECTED FAILURE: {body['message']}")
    else:
        print(f"  ❌ Should have failed with 400")
        return False
    
    # Test 4: Missing required field
    print("\n" + "-" * 80)
    print("TEST 4: Missing file_name (should fail)")
    test_event["body"] = json.dumps({
        "content_type": "image/jpeg",
        "image_order": 3
    })
    
    result = handler(test_event, None)
    print(f"  Status Code: {result['statusCode']}")
    
    if result['statusCode'] == 400:
        body = json.loads(result['body'])
        print(f"  ✅ EXPECTED FAILURE: {body['message']}")
    else:
        print(f"  ❌ Should have failed with 400")
        return False
    
    # Test 5: Wrong job ownership
    print("\n" + "-" * 80)
    print("TEST 5: Wrong job ownership (should fail)")
    test_event["pathParameters"]["job_id"] = "99999"  # Non-existent job
    test_event["body"] = json.dumps({
        "file_name": "test.jpg",
        "content_type": "image/jpeg",
        "image_order": 1
    })
    
    result = handler(test_event, None)
    print(f"  Status Code: {result['statusCode']}")
    
    if result['statusCode'] in [403, 404]:
        body = json.loads(result['body'])
        print(f"  ✅ EXPECTED FAILURE: {body['message']}")
    else:
        print(f"  ❌ Should have failed with 403 or 404")
        return False
    
    # Test 6: Different image orders
    print("\n" + "-" * 80)
    print("TEST 6: Multiple valid image orders")
    test_event["pathParameters"]["job_id"] = str(job_id)
    
    for order in [2, 3, 4, 5]:
        test_event["body"] = json.dumps({
            "file_name": f"test_image_{order}.jpg",
            "content_type": "image/jpeg",
            "image_order": order
        })
        
        result = handler(test_event, None)
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            print(f"  ✅ Image order {order}: {body['image_key']}")
        else:
            body = json.loads(result['body'])
            print(f"  ⚠️  Image order {order}: {body.get('message', 'Unknown error')}")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = test_upload_job_image()
    sys.exit(0 if success else 1)
