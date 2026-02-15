#!/usr/bin/env python3
"""
Test script for GET /customer/reviews endpoint
Tests the get_customer_reviews_to_providers Lambda function
"""

import sys
import json
import importlib.util

# Load the handler module dynamically
spec = importlib.util.spec_from_file_location(
    "handler",
    "lambda/reviews/get_customer_reviews_to_providers/handler.py"
)
handler_module = importlib.util.module_from_spec(spec)
sys.modules["handler"] = handler_module
spec.loader.exec_module(handler_module)

handler = handler_module.handler


def test_customer_reviews():
    """Test getting reviews written by customers"""
    
    print("=" * 70)
    print("Testing GET /customer/reviews")
    print("=" * 70)
    
    # Test 1: Get reviews by customer 12 (has 1 review)
    print("\n📋 Test 1: Customer 12 (AjayTest Persaud) - Has 1 review")
    print("-" * 70)
    event1 = {
        "customer_id": 12,
        "sort": "newest",
        "limit": 10,
        "offset": 0
    }
    
    result1 = handler(event1, None)
    print(f"Status Code: {result1['statusCode']}")
    body1 = json.loads(result1['body'])
    print(json.dumps(body1, indent=2))
    
    # Test 2: Get reviews by customer 13 (has 2 reviews)
    print("\n📋 Test 2: Customer 13 (Test Yang) - Has 2 reviews")
    print("-" * 70)
    event2 = {
        "customer_id": 13,
        "sort": "newest",
        "limit": 10,
        "offset": 0
    }
    
    result2 = handler(event2, None)
    print(f"Status Code: {result2['statusCode']}")
    body2 = json.loads(result2['body'])
    print(json.dumps(body2, indent=2))
    
    # Test 3: Sort by highest rating
    print("\n📋 Test 3: Customer 13 - Sort by highest rating")
    print("-" * 70)
    event3 = {
        "customer_id": 13,
        "sort": "highest_rating",
        "limit": 5,
        "offset": 0
    }
    
    result3 = handler(event3, None)
    print(f"Status Code: {result3['statusCode']}")
    body3 = json.loads(result3['body'])
    print(json.dumps(body3, indent=2))
    
    # Test 4: Pagination test (limit=1)
    print("\n📋 Test 4: Customer 13 - Pagination (limit=1, offset=0)")
    print("-" * 70)
    event4 = {
        "customer_id": 13,
        "sort": "newest",
        "limit": 1,
        "offset": 0
    }
    
    result4 = handler(event4, None)
    print(f"Status Code: {result4['statusCode']}")
    body4 = json.loads(result4['body'])
    print(json.dumps(body4, indent=2))
    
    # Test 5: Pagination test (limit=1, offset=1)
    print("\n📋 Test 5: Customer 13 - Pagination (limit=1, offset=1)")
    print("-" * 70)
    event5 = {
        "customer_id": 13,
        "sort": "newest",
        "limit": 1,
        "offset": 1
    }
    
    result5 = handler(event5, None)
    print(f"Status Code: {result5['statusCode']}")
    body5 = json.loads(result5['body'])
    print(json.dumps(body5, indent=2))
    
    # Test 6: Customer with no reviews
    print("\n📋 Test 6: Customer 1 (Test User) - No reviews")
    print("-" * 70)
    event6 = {
        "customer_id": 1,
        "sort": "newest",
        "limit": 10,
        "offset": 0
    }
    
    result6 = handler(event6, None)
    print(f"Status Code: {result6['statusCode']}")
    body6 = json.loads(result6['body'])
    print(json.dumps(body6, indent=2))
    
    # Test 7: Invalid sort parameter
    print("\n📋 Test 7: Invalid sort parameter")
    print("-" * 70)
    event7 = {
        "customer_id": 13,
        "sort": "invalid_sort",
        "limit": 10,
        "offset": 0
    }
    
    result7 = handler(event7, None)
    print(f"Status Code: {result7['statusCode']}")
    body7 = json.loads(result7['body'])
    print(json.dumps(body7, indent=2))
    
    print("\n" + "=" * 70)
    print("✅ Testing complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_customer_reviews()
