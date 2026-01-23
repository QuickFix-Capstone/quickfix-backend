#!/usr/bin/env python3
"""
Local test script for update_ratings Lambda function.

This script tests the rating calculation logic by directly invoking the handler.
For testing the deployed Lambda on AWS, use AWS CLI or boto3.
"""

import json
import sys
import os

# Add parent directories to path so we can import the handler
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from lambda.reviews.update_ratings.handler import handler


def test_update_provider_rating():
    """Test updating a provider's rating."""
    print("=" * 70)
    print("TEST 1: Update Provider Rating")
    print("=" * 70)

    event = {
        "reviewee_id": 1,
        "reviewee_type": "provider"
    }

    print(f"Input: {json.dumps(event, indent=2)}")
    result = handler(event, None)

    print(f"\nStatus Code: {result['statusCode']}")
    print(f"Response Body:")
    print(json.dumps(json.loads(result['body']), indent=2))

    assert result['statusCode'] == 200, "Expected status code 200"
    print("✅ PASSED\n")


def test_update_customer_rating():
    """Test updating a customer's rating."""
    print("=" * 70)
    print("TEST 2: Update Customer Rating")
    print("=" * 70)

    event = {
        "reviewee_id": 1,
        "reviewee_type": "customer"
    }

    print(f"Input: {json.dumps(event, indent=2)}")
    result = handler(event, None)

    print(f"\nStatus Code: {result['statusCode']}")
    print(f"Response Body:")
    print(json.dumps(json.loads(result['body']), indent=2))

    assert result['statusCode'] == 200, "Expected status code 200"
    print("✅ PASSED\n")


def test_invalid_reviewee_type():
    """Test with invalid reviewee_type."""
    print("=" * 70)
    print("TEST 3: Invalid reviewee_type (Should Fail)")
    print("=" * 70)

    event = {
        "reviewee_id": 1,
        "reviewee_type": "invalid_type"
    }

    print(f"Input: {json.dumps(event, indent=2)}")
    result = handler(event, None)

    print(f"\nStatus Code: {result['statusCode']}")
    print(f"Response Body:")
    print(json.dumps(json.loads(result['body']), indent=2))

    assert result['statusCode'] == 400, "Expected status code 400"
    print("✅ PASSED (Correctly rejected)\n")


def test_missing_reviewee_id():
    """Test with missing reviewee_id."""
    print("=" * 70)
    print("TEST 4: Missing reviewee_id (Should Fail)")
    print("=" * 70)

    event = {
        "reviewee_type": "provider"
    }

    print(f"Input: {json.dumps(event, indent=2)}")
    result = handler(event, None)

    print(f"\nStatus Code: {result['statusCode']}")
    print(f"Response Body:")
    print(json.dumps(json.loads(result['body']), indent=2))

    assert result['statusCode'] == 400, "Expected status code 400"
    print("✅ PASSED (Correctly rejected)\n")


def test_invalid_reviewee_id():
    """Test with invalid reviewee_id (negative number)."""
    print("=" * 70)
    print("TEST 5: Invalid reviewee_id (Negative)")
    print("=" * 70)

    event = {
        "reviewee_id": -1,
        "reviewee_type": "provider"
    }

    print(f"Input: {json.dumps(event, indent=2)}")
    result = handler(event, None)

    print(f"\nStatus Code: {result['statusCode']}")
    print(f"Response Body:")
    print(json.dumps(json.loads(result['body']), indent=2))

    assert result['statusCode'] == 400, "Expected status code 400"
    print("✅ PASSED (Correctly rejected)\n")


def test_api_gateway_format():
    """Test with API Gateway event format (body as JSON string)."""
    print("=" * 70)
    print("TEST 6: API Gateway Event Format")
    print("=" * 70)

    event = {
        "body": json.dumps({
            "reviewee_id": 1,
            "reviewee_type": "provider"
        })
    }

    print(f"Input: API Gateway format with body as JSON string")
    result = handler(event, None)

    print(f"\nStatus Code: {result['statusCode']}")
    print(f"Response Body:")
    print(json.dumps(json.loads(result['body']), indent=2))

    assert result['statusCode'] == 200, "Expected status code 200"
    print("✅ PASSED\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("RUNNING UPDATE_RATINGS LAMBDA TESTS")
    print("=" * 70 + "\n")

    try:
        # Run all tests
        test_update_provider_rating()
        test_update_customer_rating()
        test_invalid_reviewee_type()
        test_missing_reviewee_id()
        test_invalid_reviewee_id()
        test_api_gateway_format()

        print("=" * 70)
        print("ALL TESTS PASSED! ✅")
        print("=" * 70)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
