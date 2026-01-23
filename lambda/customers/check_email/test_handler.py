#!/usr/bin/env python3
"""
Test script for check_email handler
"""
import json
import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import the handler function
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handler import handler


def test_email_exists():
    """Test with an email that exists in the database"""
    event = {
        "queryStringParameters": {
            "email": "alice.johnson@example.com"
        }
    }
    
    print("🔍 Test 1: Checking existing email (alice.johnson@example.com)")
    response = handler(event, None)
    print(f"Status Code: {response['statusCode']}")
    print(f"Response: {response['body']}")
    print()


def test_email_not_exists():
    """Test with an email that doesn't exist"""
    event = {
        "queryStringParameters": {
            "email": "nonexistent@example.com"
        }
    }
    
    print("🔍 Test 2: Checking non-existent email (nonexistent@example.com)")
    response = handler(event, None)
    print(f"Status Code: {response['statusCode']}")
    print(f"Response: {response['body']}")
    print()


def test_missing_email():
    """Test with missing email parameter"""
    event = {
        "queryStringParameters": {}
    }
    
    print("🔍 Test 3: Missing email parameter")
    response = handler(event, None)
    print(f"Status Code: {response['statusCode']}")
    print(f"Response: {response['body']}")
    print()


def test_no_query_params():
    """Test with no query parameters at all"""
    event = {}
    
    print("🔍 Test 4: No query parameters")
    response = handler(event, None)
    print(f"Status Code: {response['statusCode']}")
    print(f"Response: {response['body']}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Testing check_email handler")
    print("=" * 60)
    print()
    
    test_email_exists()
    test_email_not_exists()
    test_missing_email()
    test_no_query_params()
    
    print("=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
