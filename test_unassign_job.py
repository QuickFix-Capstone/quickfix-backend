#!/usr/bin/env python3
"""
Test script for unassign_job endpoint
This simulates what happens when a real authenticated user calls the API
"""

import json

# Simulate the event that API Gateway sends to Lambda after JWT validation
test_event = {
    "requestContext": {
        "authorizer": {
            "jwt": {
                "claims": {
                    # This is the test customer's cognito_sub
                    "sub": "415b3510-a0a1-708e-6a02-dc457aec9ecc"
                }
            }
        }
    },
    "pathParameters": {
        "job_id": "4"  # Job 4 should be in "assigned" status
    }
}

print("=" * 60)
print("Testing unassign_job Lambda function")
print("=" * 60)
print(f"\nTest Event:")
print(json.dumps(test_event, indent=2))
print("\n" + "=" * 60)

# Import and call the handler
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lambda/jobs/unassign_job'))
from handler import handler

result = handler(test_event, None)

print("\nResponse:")
print(json.dumps(json.loads(result['body']) if isinstance(result.get('body'), str) else result, indent=2))
print(f"\nStatus Code: {result['statusCode']}")
print("=" * 60)

# Verify the result
if result['statusCode'] == 200:
    body = json.loads(result['body'])
    print("\n✅ SUCCESS!")
    print(f"   Job status changed to: {body['job']['status']}")
    print(f"   Assigned provider: {body['job']['assigned_provider_id']}")
else:
    print(f"\n❌ FAILED with status {result['statusCode']}")
    body = json.loads(result['body'])
    print(f"   Message: {body.get('message', 'Unknown error')}")
