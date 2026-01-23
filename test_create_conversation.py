#!/usr/bin/env python3
"""
Test script for create_conversation Lambda function
"""
import json
import sys
import os
import importlib.util

# Load handler module directly
spec = importlib.util.spec_from_file_location(
    "handler",
    "lambda/messages/create_conversation/handler.py"
)
handler_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handler_module)
handler = handler_module.handler

def test_create_conversation():
    """Test creating a conversation between customer and provider"""
    
    print("=" * 80)
    print("Testing create_conversation Lambda Function")
    print("=" * 80)
    
    # Test 1: Create conversation between customer 1 and provider
    print("\n📝 Test 1: Create new conversation")
    print("-" * 80)
    
    test_event = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "415b3510-a0a1-708e-6a02-dc457aec9ecc"  # Customer cognito_sub
                    }
                }
            }
        },
        "body": json.dumps({
            "otherUserId": "SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c",
            "jobId": "1001"
        })
    }
    
    result = handler(test_event, None)
    
    print(f"Status Code: {result['statusCode']}")
    response_body = json.loads(result['body'])
    print(f"Response:\n{json.dumps(response_body, indent=2)}")
    
    if result['statusCode'] == 201:
        print("✅ Test 1 PASSED: Conversation created")
        conversation_id = response_body.get('conversationId')
    elif result['statusCode'] == 200:
        print("✅ Test 1 PASSED: Conversation already exists")
        conversation_id = response_body.get('conversationId')
    else:
        print("❌ Test 1 FAILED")
        return
    
    # Test 2: Try to create same conversation again (should return existing)
    print("\n📝 Test 2: Try to create duplicate conversation")
    print("-" * 80)
    
    result2 = handler(test_event, None)
    response_body2 = json.loads(result2['body'])
    
    print(f"Status Code: {result2['statusCode']}")
    print(f"Response:\n{json.dumps(response_body2, indent=2)}")
    
    if result2['statusCode'] == 200 and 'already exists' in response_body2.get('message', ''):
        print("✅ Test 2 PASSED: Returns existing conversation")
    else:
        print("❌ Test 2 FAILED: Should return existing conversation")
    
    # Test 3: Missing otherUserId
    print("\n📝 Test 3: Missing otherUserId (should fail)")
    print("-" * 80)
    
    test_event_invalid = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "415b3510-a0a1-708e-6a02-dc457aec9ecc"
                    }
                }
            }
        },
        "body": json.dumps({
            "jobId": "1001"
        })
    }
    
    result3 = handler(test_event_invalid, None)
    response_body3 = json.loads(result3['body'])
    
    print(f"Status Code: {result3['statusCode']}")
    print(f"Response:\n{json.dumps(response_body3, indent=2)}")
    
    if result3['statusCode'] == 400:
        print("✅ Test 3 PASSED: Validation error for missing otherUserId")
    else:
        print("❌ Test 3 FAILED: Should return 400 for missing otherUserId")
    
    # Test 4: Invalid user
    print("\n📝 Test 4: Invalid otherUserId (should fail)")
    print("-" * 80)
    
    test_event_invalid_user = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "415b3510-a0a1-708e-6a02-dc457aec9ecc"
                    }
                }
            }
        },
        "body": json.dumps({
            "otherUserId": "SP-nonexistent",
            "jobId": "1001"
        })
    }
    
    result4 = handler(test_event_invalid_user, None)
    response_body4 = json.loads(result4['body'])
    
    print(f"Status Code: {result4['statusCode']}")
    print(f"Response:\n{json.dumps(response_body4, indent=2)}")
    
    if result4['statusCode'] == 404:
        print("✅ Test 4 PASSED: Returns 404 for invalid user")
    else:
        print("❌ Test 4 FAILED: Should return 404 for invalid user")
    
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print("All basic tests completed!")
    print(f"Conversation ID created: {conversation_id}")

if __name__ == "__main__":
    test_create_conversation()
