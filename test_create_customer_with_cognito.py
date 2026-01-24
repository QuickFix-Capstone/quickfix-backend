#!/usr/bin/env python3
"""
Test script for create_customer Lambda with Cognito group assignment.
Tests JWT extraction and group assignment functionality.
"""

import json
import base64
import sys
import os

# Add parent directory to path to import handler
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lambda/customers/create_customer'))

from handler import handler


def create_mock_jwt(email: str) -> str:
    """Create a mock JWT token with email claim for testing."""
    payload = {
        "email": email,
        "sub": "test-sub-123",
        "cognito:username": email,
        "cognito:groups": []  # User doesn't have groups yet
    }
    # Encode payload as base64
    encoded_payload = base64.b64encode(json.dumps(payload).encode()).decode()
    # Create a fake JWT (header.payload.signature)
    return f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.{encoded_payload}.fake_signature"


def test_create_customer_with_cognito():
    """Test customer creation with Cognito group assignment."""
    
    test_email = f"test-cognito-{int(os.time() if hasattr(os, 'time') else 1234567890)}@example.com"
    
    # Create test event with Authorization header
    test_event = {
        "headers": {
            "Authorization": f"Bearer {create_mock_jwt(test_email)}"
        },
        "body": json.dumps({
            "first_name": "Test",
            "last_name": "CognitoUser",
            "email": test_email,
            "phone": "123-456-7890",
            "address": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "postal_code": "T3S 7T1"
        })
    }
    
    print("🔍 Testing create_customer with Cognito group assignment...")
    print(f"📧 Test email: {test_email}")
    print()
    
    # Run the handler
    try:
        result = handler(test_event, None)
        print("✅ Handler executed successfully")
        print()
        print("Response:")
        print(json.dumps(result, indent=2))
        
        # Check response
        if result.get('statusCode') == 201:
            print()
            print("✅ Customer created successfully!")
            print("📝 Check CloudWatch logs for Cognito group assignment messages:")
            print("   - Look for: '✅ Successfully added ... to customer group'")
            print("   - Or: '⚠️ Failed to add user to group' (if IAM permissions not set)")
        else:
            print()
            print(f"⚠️ Unexpected status code: {result.get('statusCode')}")
            
    except Exception as e:
        print(f"❌ Error running handler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("Create Customer with Cognito Group Assignment - Test")
    print("=" * 60)
    print()
    
    # Check if running locally or need to set env vars
    if not os.environ.get('MYSQL_HOST'):
        print("⚠️ Warning: Database environment variables not set")
        print("   Make sure to run: source .env or set variables manually")
        print()
    
    test_create_customer_with_cognito()
    
    print()
    print("=" * 60)
    print("Test complete!")
    print()
    print("Next steps:")
    print("1. Deploy the Lambda: cd deploy && ./deploy_create_customer.sh")
    print("2. Update IAM permissions (see implementation_plan.md)")
    print("3. Test with real customer registration")
    print("=" * 60)
