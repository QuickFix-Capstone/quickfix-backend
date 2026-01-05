#!/usr/bin/env python3
"""
Local test for list_conversations Lambda function
"""
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

# Set environment variables for MySQL
os.environ['MYSQL_HOST'] = 'quickfix-mysql.cno624c2aarh.us-east-2.rds.amazonaws.com'
os.environ['MYSQL_USER'] = 'admin'
os.environ['MYSQL_PASSWORD'] = 'QuickFix123!'
os.environ['MYSQL_DB'] = 'quickfix'
os.environ['MYSQL_PORT'] = '3306'

# Import handler
import importlib.util
spec = importlib.util.spec_from_file_location(
    "handler",
    "lambda/messages/list_conversations/handler.py"
)
handler_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handler_module)
handler = handler_module.handler

def test_list_conversations():
    """Test listing conversations for a user"""
    
    print("=" * 80)
    print("Testing list_conversations Lambda Function")
    print("=" * 80)
    
    # Test 1: List conversations for customer
    print("\n📝 Test 1: List conversations for customer (cognito_sub from JWT)")
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
        "queryStringParameters": {
            "limit": "10"
        }
    }
    
    try:
        result = handler(test_event, None)
        
        print(f"Status Code: {result['statusCode']}")
        response_body = json.loads(result['body'])
        print(f"Response:\n{json.dumps(response_body, indent=2)}")
        
        if result['statusCode'] == 200:
            print(f"\n✅ Test 1 PASSED: Found {response_body.get('total', 0)} conversations")
            
            # Display conversations in a nice format
            if response_body.get('conversations'):
                print("\nConversations:")
                for conv in response_body['conversations']:
                    print(f"\n  Conversation ID: {conv['conversationId']}")
                    print(f"  Other User: {conv['otherUser']['name']} ({conv['otherUser']['type']})")
                    if conv.get('jobId'):
                        print(f"  Job: {conv.get('jobTitle', 'N/A')} (ID: {conv['jobId']})")
                    print(f"  Last Message: {conv['lastMessage']['preview']}")
                    print(f"  Unread Count: {conv['unreadCount']}")
        else:
            print("❌ Test 1 FAILED")
            
    except Exception as e:
        print(f"❌ Test 1 FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Test with limit parameter
    print("\n📝 Test 2: Test with limit=5")
    print("-" * 80)
    
    test_event_limit = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "415b3510-a0a1-708e-6a02-dc457aec9ecc"
                    }
                }
            }
        },
        "queryStringParameters": {
            "limit": "5"
        }
    }
    
    try:
        result2 = handler(test_event_limit, None)
        response_body2 = json.loads(result2['body'])
        
        print(f"Status Code: {result2['statusCode']}")
        print(f"Total conversations returned: {response_body2.get('total', 0)}")
        
        if result2['statusCode'] == 200 and response_body2.get('total', 0) <= 5:
            print("✅ Test 2 PASSED: Limit parameter works")
        else:
            print("❌ Test 2 FAILED")
            
    except Exception as e:
        print(f"❌ Test 2 FAILED with exception: {e}")
    
    # Test 3: Test without limit (should default to 20)
    print("\n📝 Test 3: Test without limit parameter (should default to 20)")
    print("-" * 80)
    
    test_event_no_limit = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "415b3510-a0a1-708e-6a02-dc457aec9ecc"
                    }
                }
            }
        }
    }
    
    try:
        result3 = handler(test_event_no_limit, None)
        response_body3 = json.loads(result3['body'])
        
        print(f"Status Code: {result3['statusCode']}")
        print(f"Total conversations returned: {response_body3.get('total', 0)}")
        
        if result3['statusCode'] == 200:
            print("✅ Test 3 PASSED: Default limit works")
        else:
            print("❌ Test 3 FAILED")
            
    except Exception as e:
        print(f"❌ Test 3 FAILED with exception: {e}")
    
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print("All tests completed!")

if __name__ == "__main__":
    test_list_conversations()
