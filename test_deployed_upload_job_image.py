#!/usr/bin/env python3
"""
Test the DEPLOYED upload_job_image Lambda via API Gateway.

This script will:
1. Get a customer JWT token
2. Find a job owned by that customer
3. Call the deployed API endpoint
4. Verify presigned URL generation
"""

import sys
import os
import json
import requests

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.db.rds_main import get_connection


# API Configuration
API_BASE_URL = "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com"
UPLOAD_URL_ENDPOINT = "/jobs/{job_id}/images/upload-url"


def get_customer_token():
    """Get a customer JWT token for testing."""
    # You'll need to replace this with actual token retrieval
    # For now, using a placeholder - you should run get_customer_idtoken.py
    print("⚠️  You need to provide a valid customer JWT token")
    print("   Run: python scripts/get_customer_idtoken.py")
    token = input("Enter customer JWT token: ").strip()
    return token


def find_customer_job(cognito_sub):
    """Find a job owned by the customer."""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT j.job_id, j.customer_id, j.title
                FROM jobs j
                JOIN customers c ON j.customer_id = c.customer_id
                WHERE c.cognito_sub = %s
                LIMIT 1
            """, (cognito_sub,))
            
            result = cur.fetchone()
            if result:
                print(f"✅ Found job: job_id={result['job_id']}, title='{result['title']}'")
                return result['job_id']
            else:
                print("❌ No jobs found for this customer")
                return None
    finally:
        conn.close()


def test_deployed_api(jwt_token, job_id):
    """Test the deployed API endpoint."""
    
    print("\n" + "=" * 80)
    print("🧪 TESTING DEPLOYED UPLOAD_JOB_IMAGE API")
    print("=" * 80)
    
    url = API_BASE_URL + UPLOAD_URL_ENDPOINT.format(job_id=job_id)
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Valid request
    print("\n" + "-" * 80)
    print("TEST 1: Valid upload request")
    print(f"URL: {url}")
    
    payload = {
        "file_name": "deployed_test_photo.jpg",
        "content_type": "image/jpeg",
        "image_order": 1
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ SUCCESS!")
        print(f"Message: {data.get('message')}")
        print(f"Upload URL: {data.get('upload_url', '')[:60]}...")
        print(f"Image Key: {data.get('image_key')}")
        print(f"Expires In: {data.get('expires_in')} seconds")
    else:
        print(f"❌ FAILED")
        print(f"Response: {response.text}")
        return False
    
    # Test 2: Invalid content type
    print("\n" + "-" * 80)
    print("TEST 2: Invalid content type (should fail)")
    
    payload = {
        "file_name": "test.pdf",
        "content_type": "application/pdf",
        "image_order": 2
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        data = response.json()
        print(f"✅ EXPECTED FAILURE: {data.get('message')}")
    else:
        print(f"❌ Should have failed with 400")
        print(f"Response: {response.text}")
    
    # Test 3: Invalid image_order
    print("\n" + "-" * 80)
    print("TEST 3: Invalid image_order (should fail)")
    
    payload = {
        "file_name": "test.jpg",
        "content_type": "image/jpeg",
        "image_order": 10
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        data = response.json()
        print(f"✅ EXPECTED FAILURE: {data.get('message')}")
    else:
        print(f"❌ Should have failed with 400")
        print(f"Response: {response.text}")
    
    # Test 4: Multiple image orders
    print("\n" + "-" * 80)
    print("TEST 4: Multiple valid image orders")
    
    for order in [2, 3, 4, 5]:
        payload = {
            "file_name": f"test_image_{order}.jpg",
            "content_type": "image/jpeg",
            "image_order": order
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Image order {order}: {data.get('image_key')}")
        else:
            data = response.json()
            print(f"  ⚠️  Image order {order}: {data.get('message', 'Unknown error')}")
    
    print("\n" + "=" * 80)
    print("✅ API TESTS COMPLETED!")
    print("=" * 80)
    return True


def main():
    print("=" * 80)
    print("🚀 DEPLOYED API TEST FOR UPLOAD_JOB_IMAGE")
    print("=" * 80)
    
    # Get JWT token
    print("\n📋 Step 1: Get customer JWT token")
    jwt_token = get_customer_token()
    
    if not jwt_token:
        print("❌ No JWT token provided")
        return False
    
    # Decode token to get cognito_sub (simplified - in production use proper JWT library)
    try:
        import base64
        # JWT format: header.payload.signature
        payload_part = jwt_token.split('.')[1]
        # Add padding if needed
        padding = 4 - len(payload_part) % 4
        if padding != 4:
            payload_part += '=' * padding
        
        decoded = base64.b64decode(payload_part)
        token_data = json.loads(decoded)
        cognito_sub = token_data.get('sub')
        print(f"✅ Token decoded, cognito_sub: {cognito_sub}")
    except Exception as e:
        print(f"❌ Failed to decode token: {e}")
        print("   Trying to find any job for testing...")
        cognito_sub = None
    
    # Find a job
    print("\n📋 Step 2: Find a job for testing")
    if cognito_sub:
        job_id = find_customer_job(cognito_sub)
    else:
        # Fallback: use any job
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT job_id FROM jobs LIMIT 1")
            result = cur.fetchone()
            job_id = result['job_id'] if result else None
        conn.close()
    
    if not job_id:
        print("❌ No job found for testing")
        return False
    
    # Test the API
    print("\n📋 Step 3: Test the deployed API")
    success = test_deployed_api(jwt_token, job_id)
    
    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
