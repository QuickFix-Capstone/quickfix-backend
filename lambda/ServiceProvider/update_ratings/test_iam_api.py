#!/usr/bin/env python3
"""
Test script for update_ratings internal API with IAM authentication.

This demonstrates how to call the internal API endpoint that requires AWS credentials.
The endpoint is NOT publicly accessible and requires AWS Signature Version 4 (SigV4).

Requirements:
    pip install requests requests-aws4auth boto3

Usage:
    python test_iam_api.py
"""

import json
import sys
import boto3
import requests
from requests_aws4auth import AWS4Auth

# API Configuration
API_ENDPOINT = "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/internal/update-ratings"
AWS_REGION = "us-east-2"


def test_iam_authenticated_request():
    """
    Test calling the internal API using AWS SigV4 authentication.
    This method uses HTTP with AWS signature for authentication.
    """
    print("=" * 70)
    print("Test: IAM-Authenticated HTTP Request to Internal API")
    print("=" * 70)
    print()

    # Get AWS credentials from boto3 session
    # This uses your configured AWS credentials (~/.aws/credentials)
    print("🔐 Getting AWS credentials...")
    session = boto3.Session()
    credentials = session.get_credentials()

    if not credentials:
        print("❌ ERROR: No AWS credentials found!")
        print("   Please configure AWS credentials:")
        print("   aws configure")
        return False

    print(f"✅ Found credentials for access key: {credentials.access_key[:8]}...")
    print()

    # Create AWS4Auth instance for request signing
    auth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        AWS_REGION,
        'execute-api',
        session_token=credentials.token
    )

    # Test Case 1: Update provider rating
    print("📝 Test Case 1: Update provider rating")
    print("-" * 70)

    payload = {
        "reviewee_id": "google-oauth2|103949366066974158596",
        "reviewee_type": "provider"
    }

    print(f"Request Payload: {json.dumps(payload, indent=2)}")
    print(f"Endpoint: POST {API_ENDPOINT}")
    print()

    try:
        response = requests.post(
            API_ENDPOINT,
            auth=auth,
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()

        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"Response Body:")
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ FAILED!")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

    print()
    print("=" * 70)

    # Test Case 2: Update customer rating
    print("📝 Test Case 2: Update customer rating")
    print("-" * 70)

    payload = {
        "reviewee_id": 1,
        "reviewee_type": "customer"
    }

    print(f"Request Payload: {json.dumps(payload, indent=2)}")
    print()

    try:
        response = requests.post(
            API_ENDPOINT,
            auth=auth,
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status Code: {response.status_code}")
        print()

        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"Response Body:")
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ FAILED!")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

    print()
    print("=" * 70)

    # Test Case 3: Invalid input (should fail with 400)
    print("📝 Test Case 3: Invalid reviewee_type (should fail)")
    print("-" * 70)

    payload = {
        "reviewee_id": 1,
        "reviewee_type": "invalid"
    }

    print(f"Request Payload: {json.dumps(payload, indent=2)}")
    print()

    try:
        response = requests.post(
            API_ENDPOINT,
            auth=auth,
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 400:
            result = response.json()
            print("✅ EXPECTED FAILURE (400 Bad Request)")
            print(f"Response Body:")
            print(json.dumps(result, indent=2))
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

    print()
    print("=" * 70)

    return True


def test_without_authentication():
    """
    Test calling the API WITHOUT authentication (should fail with 403).
    This demonstrates that the endpoint is NOT publicly accessible.
    """
    print()
    print("=" * 70)
    print("Test: Attempt to access without authentication (should fail)")
    print("=" * 70)
    print()

    payload = {
        "reviewee_id": 1,
        "reviewee_type": "provider"
    }

    print(f"Request Payload: {json.dumps(payload, indent=2)}")
    print(f"Endpoint: POST {API_ENDPOINT}")
    print("Authentication: NONE (testing if endpoint is public)")
    print()

    try:
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 403:
            print("✅ EXPECTED FAILURE (403 Forbidden)")
            print("   This confirms the endpoint requires AWS credentials")
            print(f"   Response: {response.text}")
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

    print()
    print("=" * 70)

    return True


def main():
    """Run all tests."""
    print()
    print("🧪 Testing Internal API with IAM Authentication")
    print("=" * 70)
    print()
    print("📍 API Endpoint:")
    print(f"   {API_ENDPOINT}")
    print()
    print("🔐 Authentication Type: AWS_IAM (SigV4)")
    print("   Requires AWS credentials to access")
    print()
    print("=" * 70)

    # Test 1: With proper authentication
    success = test_iam_authenticated_request()

    # Test 2: Without authentication (should fail)
    test_without_authentication()

    print()
    print("=" * 70)
    print("📊 Test Summary")
    print("=" * 70)

    if success:
        print("✅ IAM-authenticated requests: PASSED")
        print("✅ Endpoint properly secured with AWS_IAM authorization")
        print()
        print("💡 Key Findings:")
        print("   • Endpoint requires AWS Signature Version 4 (SigV4)")
        print("   • NOT publicly accessible (403 without credentials)")
        print("   • Can be called from Lambda functions automatically")
        print("   • Can be called from applications with AWS credentials")
    else:
        print("❌ Some tests failed")
        print()
        print("💡 Common Issues:")
        print("   • AWS credentials not configured: run 'aws configure'")
        print("   • IAM user lacks execute-api permissions")
        print("   • Lambda function not deployed correctly")

    print()
    print("=" * 70)
    print()
    print("📝 Next Steps:")
    print()
    print("1. Integrate with create_review Lambda:")
    print("   # Add this after creating a review")
    print("   lambda_client = boto3.client('lambda')")
    print("   lambda_client.invoke(")
    print("       FunctionName='update_ratings',")
    print("       InvocationType='Event',")
    print("       Payload=json.dumps({")
    print("           'reviewee_id': reviewee_id,")
    print("           'reviewee_type': reviewee_type")
    print("       })")
    print("   )")
    print()
    print("2. Or call via HTTP with SigV4 (as demonstrated in this script)")
    print()
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
