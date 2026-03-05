#!/usr/bin/env python3
"""
Test script for invoking the deployed update_ratings Lambda function on AWS.

This script uses boto3 to invoke the Lambda function deployed to AWS
and verify it works correctly with real database data.
"""

import json
import boto3
import sys

# AWS Configuration
LAMBDA_FUNCTION_NAME = "update_ratings"
AWS_REGION = "us-east-2"

# Initialize Lambda client
lambda_client = boto3.client('lambda', region_name=AWS_REGION)


def invoke_lambda(payload, invocation_type='RequestResponse'):
    """
    Invoke the Lambda function with the given payload.

    Args:
        payload: Dictionary to send to Lambda
        invocation_type: 'RequestResponse' (sync) or 'Event' (async)

    Returns:
        Response from Lambda
    """
    print(f"📤 Invoking Lambda: {LAMBDA_FUNCTION_NAME}")
    print(f"   Invocation Type: {invocation_type}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")

    response = lambda_client.invoke(
        FunctionName=LAMBDA_FUNCTION_NAME,
        InvocationType=invocation_type,
        Payload=json.dumps(payload)
    )

    if invocation_type == 'RequestResponse':
        # Read response for synchronous invocation
        response_payload = json.loads(response['Payload'].read())
        print(f"📥 Response:")
        print(f"   Status Code: {response['StatusCode']}")
        print(f"   Lambda Response: {json.dumps(response_payload, indent=2)}")
        return response_payload
    else:
        # Async invocation - no response body
        print(f"📥 Async Invocation Status: {response['StatusCode']}")
        return None


def test_update_provider_rating():
    """Test updating a provider's rating (synchronous)."""
    print("\n" + "=" * 70)
    print("TEST 1: Update Provider Rating (Synchronous)")
    print("=" * 70)

    payload = {
        "reviewee_id": 1,
        "reviewee_type": "provider"
    }

    response = invoke_lambda(payload, 'RequestResponse')

    # Parse the Lambda response
    if response and 'statusCode' in response:
        body = json.loads(response['body'])
        print(f"\n✅ Lambda executed successfully!")
        print(f"   Rating Info: {json.dumps(body.get('rating_info', {}), indent=2)}")
        return response['statusCode'] == 200
    else:
        print("❌ Lambda invocation failed")
        return False


def test_update_customer_rating():
    """Test updating a customer's rating (synchronous)."""
    print("\n" + "=" * 70)
    print("TEST 2: Update Customer Rating (Synchronous)")
    print("=" * 70)

    payload = {
        "reviewee_id": 1,
        "reviewee_type": "customer"
    }

    response = invoke_lambda(payload, 'RequestResponse')

    if response and 'statusCode' in response:
        body = json.loads(response['body'])
        print(f"\n✅ Lambda executed successfully!")
        print(f"   Rating Info: {json.dumps(body.get('rating_info', {}), indent=2)}")
        return response['statusCode'] == 200
    else:
        print("❌ Lambda invocation failed")
        return False


def test_async_invocation():
    """Test asynchronous invocation (fire and forget)."""
    print("\n" + "=" * 70)
    print("TEST 3: Async Invocation (Fire and Forget)")
    print("=" * 70)

    payload = {
        "reviewee_id": 1,
        "reviewee_type": "provider"
    }

    response = invoke_lambda(payload, 'Event')
    print(f"\n✅ Async invocation sent!")
    print(f"   Note: Check CloudWatch Logs to verify execution")
    return True


def test_invalid_input():
    """Test with invalid input to verify error handling."""
    print("\n" + "=" * 70)
    print("TEST 4: Invalid Input (Should Return 400)")
    print("=" * 70)

    payload = {
        "reviewee_id": 1,
        "reviewee_type": "invalid_type"
    }

    response = invoke_lambda(payload, 'RequestResponse')

    if response and 'statusCode' in response:
        body = json.loads(response['body'])
        if response['statusCode'] == 400:
            print(f"\n✅ Error correctly handled!")
            print(f"   Error Message: {body.get('message', 'N/A')}")
            return True
        else:
            print(f"❌ Expected status 400, got {response['statusCode']}")
            return False
    else:
        print("❌ Lambda invocation failed")
        return False


def get_lambda_info():
    """Get information about the deployed Lambda function."""
    print("\n" + "=" * 70)
    print("LAMBDA FUNCTION INFO")
    print("=" * 70)

    try:
        response = lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)

        config = response['Configuration']
        print(f"Function Name: {config['FunctionName']}")
        print(f"Function ARN: {config['FunctionArn']}")
        print(f"Runtime: {config['Runtime']}")
        print(f"Handler: {config['Handler']}")
        print(f"Memory Size: {config['MemorySize']} MB")
        print(f"Timeout: {config['Timeout']} seconds")
        print(f"Last Modified: {config['LastModified']}")
        print(f"State: {config.get('State', 'Unknown')}")
        print(f"Code Size: {config['CodeSize']} bytes")

        # Environment variables (redacted for security)
        env_vars = config.get('Environment', {}).get('Variables', {})
        print(f"Environment Variables:")
        for key in env_vars.keys():
            if 'PASSWORD' in key or 'SECRET' in key:
                print(f"  - {key}: ********")
            else:
                print(f"  - {key}: {env_vars[key]}")

    except Exception as e:
        print(f"❌ Error getting Lambda info: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("AWS LAMBDA INVOCATION TESTS - update_ratings")
    print("=" * 70)

    # Get Lambda info first
    get_lambda_info()

    # Run tests
    results = []

    try:
        results.append(("Update Provider Rating", test_update_provider_rating()))
        results.append(("Update Customer Rating", test_update_customer_rating()))
        results.append(("Async Invocation", test_async_invocation()))
        results.append(("Invalid Input Handling", test_invalid_input()))

        # Print summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        all_passed = True
        for test_name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name}: {status}")
            if not passed:
                all_passed = False

        if all_passed:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print("\n⚠️  SOME TESTS FAILED")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("1. Check CloudWatch Logs for detailed execution logs:")
    print(f"   aws logs tail /aws/lambda/{LAMBDA_FUNCTION_NAME} --follow")
    print("\n2. Integrate this Lambda into create_review handler:")
    print("   - Add boto3 Lambda invocation after review creation")
    print("   - Use 'Event' invocation type for async execution")
    print("\n3. Test end-to-end flow:")
    print("   - Create a review via create_review Lambda")
    print("   - Verify rating updates automatically via update_ratings")
    print("=" * 70 + "\n")
