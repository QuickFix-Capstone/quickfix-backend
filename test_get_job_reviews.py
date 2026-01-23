#!/usr/bin/env python3
"""
Test script for get_job_reviews Lambda function.
Tests with actual database data.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, '/Users/ykpfly/Desktop/capstone/quickfix_backend')

# Import the handler
import importlib.util
spec = importlib.util.spec_from_file_location(
    "handler", 
    "/Users/ykpfly/Desktop/capstone/quickfix_backend/lambda/reviews/get_job_reviews/handler.py"
)
handler_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handler_module)
handler = handler_module.handler

import json


def test_job_reviews():
    print("=" * 70)
    print("Testing GET /reviews/job/{job_id} with Database Data")
    print("=" * 70)
    
    # Test 1: Job with reviews (job_id = 1)
    print("\n📋 Test 1: Get reviews for job 1 (should have customer review)")
    print("-" * 70)
    test_event_1 = {
        "job_id": "1",
        "sort": "newest",
        "limit": 10,
        "offset": 0
    }
    
    result = handler(test_event_1, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    body = json.loads(result['body'])
    print(json.dumps(body, indent=2))
    
    if body.get('reviews'):
        print(f"\n✅ Found {len(body['reviews'])} review(s) for job 1")
    else:
        print("\n⚠️  No reviews found for job 1")
    
    # Test 2: Job with reviews (job_id = 4)
    print("\n📋 Test 2: Get reviews for job 4 (should have customer review)")
    print("-" * 70)
    test_event_2 = {
        "job_id": "4",
        "sort": "newest",
        "limit": 10,
        "offset": 0
    }
    
    result = handler(test_event_2, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    body = json.loads(result['body'])
    print(json.dumps(body, indent=2))
    
    if body.get('reviews'):
        print(f"\n✅ Found {len(body['reviews'])} review(s) for job 4")
    else:
        print("\n⚠️  No reviews found for job 4")
    
    # Test 3: Job 1001 (no reviews expected)
    print("\n📋 Test 3: Get reviews for job 1001 (no reviews expected)")
    print("-" * 70)
    test_event_3 = {
        "job_id": "1001",
        "sort": "newest",
        "limit": 10,
        "offset": 0
    }
    
    result = handler(test_event_3, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    body = json.loads(result['body'])
    print(json.dumps(body, indent=2))
    
    if result['statusCode'] == 200 and body.get('pagination', {}).get('total_count') == 0:
        print("\n✅ Correctly returned empty reviews for job with no reviews")
    
    # Test 4: Invalid job_id
    print("\n📋 Test 4: Invalid job_id (should return 400)")
    print("-" * 70)
    test_event_4 = {
        "job_id": "invalid",
    }
    
    result = handler(test_event_4, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    body = json.loads(result['body'])
    print(json.dumps(body, indent=2))
    
    if result['statusCode'] == 400:
        print("\n✅ Correctly rejected invalid job_id")
    
    # Test 5: Non-existent job
    print("\n📋 Test 5: Non-existent job (should return 404)")
    print("-" * 70)
    test_event_5 = {
        "job_id": "99999",
    }
    
    result = handler(test_event_5, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    body = json.loads(result['body'])
    print(json.dumps(body, indent=2))
    
    if result['statusCode'] == 404:
        print("\n✅ Correctly returned 404 for non-existent job")
    
    # Test 6: Test sorting
    print("\n📋 Test 6: Test sorting by highest_rating")
    print("-" * 70)
    test_event_6 = {
        "job_id": "1",
        "sort": "highest_rating",
        "limit": 10,
        "offset": 0
    }
    
    result = handler(test_event_6, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    body = json.loads(result['body'])
    print(json.dumps(body, indent=2))
    
    print("\n" + "=" * 70)
    print("✅ All tests complete!")
    print("=" * 70)

if __name__ == "__main__":
    test_job_reviews()
