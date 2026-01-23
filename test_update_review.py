#!/usr/bin/env python3
"""
Test script for update_review Lambda function.
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
    "/Users/ykpfly/Desktop/capstone/quickfix_backend/lambda/reviews/update_review/handler.py"
)
handler_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handler_module)
handler = handler_module.handler

import json
from src.db.rds_main import get_connection


def get_provider_rating(provider_id):
    """Helper to check provider's current rating."""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT average_rating, total_rating_points, total_review_count
                FROM service_providers
                WHERE provider_id = %s
                """,
                (provider_id,)
            )
            result = cur.fetchone()
            return result
    finally:
        conn.close()


def get_review(review_id):
    """Helper to get review details."""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM reviews WHERE review_id = %s",
                (review_id,)
            )
            result = cur.fetchone()
            return result
    finally:
        conn.close()


def test_update_review():
    print("=" * 70)
    print("Testing PUT /reviews/{review_id} with Database Data")
    print("=" * 70)
    
    # Use review_id = 5 (customer 1 reviewing provider 0)
    test_review_id = 5
    
    # Test 1: Check initial state
    print("\n📋 Test 1: Check initial review state")
    print("-" * 70)
    initial_review = get_review(test_review_id)
    if initial_review:
        print(f"Review ID: {initial_review['review_id']}")
        print(f"Current Rating: {initial_review['rating']}")
        print(f"Current Comment: {initial_review['comment'][:50]}...")
        print(f"Reviewer ID: {initial_review['reviewer_id']}")
        print(f"Reviewee ID: {initial_review['reviewee_id']}")
        initial_rating = initial_review['rating']
    else:
        print("❌ Review not found!")
        return
    
    # Check provider rating before update
    if initial_review['reviewee_type'] == 'provider':
        provider_rating_before = get_provider_rating(initial_review['reviewee_id'])
        if provider_rating_before:
            print(f"\nProvider Rating Before Update:")
            print(f"  Average: {provider_rating_before['average_rating']}")
            print(f"  Total Points: {provider_rating_before['total_rating_points']}")
            print(f"  Total Count: {provider_rating_before['total_review_count']}")
    
    # Test 2: Update rating only (5 → 3)
    print("\n📋 Test 2: Update rating only (5 → 3 stars)")
    print("-" * 70)
    test_event_2 = {
        "review_id": str(test_review_id),
        "user_id": initial_review['reviewer_id'],
        "user_type": initial_review['reviewer_type'],
        "rating": 3
    }
    
    result = handler(test_event_2, None)
    print(f"Status Code: {result['statusCode']}")
    body = json.loads(result['body'])
    print("Response:")
    print(json.dumps(body, indent=2))
    
    if result['statusCode'] == 200:
        print("\n✅ Rating updated successfully")
        
        # Verify rating recalculation
        if initial_review['reviewee_type'] == 'provider':
            provider_rating_after = get_provider_rating(initial_review['reviewee_id'])
            if provider_rating_after:
                print(f"\nProvider Rating After Update:")
                print(f"  Average: {provider_rating_after['average_rating']}")
                print(f"  Total Points: {provider_rating_after['total_rating_points']}")
                print(f"  Total Count: {provider_rating_after['total_review_count']}")
                
                # Calculate expected delta
                delta = 3 - initial_rating
                expected_points = provider_rating_before['total_rating_points'] + delta
                print(f"\n  Expected delta: {delta}")
                print(f"  Expected points: {expected_points}")
                
                if provider_rating_after['total_rating_points'] == expected_points:
                    print("  ✅ Rating recalculation correct!")
                else:
                    print("  ❌ Rating recalculation mismatch!")
    else:
        print(f"\n❌ Update failed: {body.get('message')}")
    
    # Test 3: Update comment only
    print("\n📋 Test 3: Update comment only")
    print("-" * 70)
    test_event_3 = {
        "review_id": str(test_review_id),
        "user_id": initial_review['reviewer_id'],
        "user_type": initial_review['reviewer_type'],
        "comment": "Updated comment: The service was good but took longer than expected. Overall satisfied."
    }
    
    result = handler(test_event_3, None)
    print(f"Status Code: {result['statusCode']}")
    body = json.loads(result['body'])
    print("Response:")
    print(json.dumps(body, indent=2))
    
    if result['statusCode'] == 200:
        print("\n✅ Comment updated successfully")
    
    # Test 4: Update both rating and comment
    print("\n📋 Test 4: Update both rating and comment")
    print("-" * 70)
    test_event_4 = {
        "review_id": str(test_review_id),
        "user_id": initial_review['reviewer_id'],
        "user_type": initial_review['reviewer_type'],
        "rating": 4,
        "comment": "Final update: Actually the service was quite good. The plumber was professional and thorough."
    }
    
    result = handler(test_event_4, None)
    print(f"Status Code: {result['statusCode']}")
    body = json.loads(result['body'])
    print("Response:")
    print(json.dumps(body, indent=2))
    
    if result['statusCode'] == 200:
        print("\n✅ Both fields updated successfully")
    
    # Test 5: Invalid rating (should fail)
    print("\n📋 Test 5: Invalid rating (should return 400)")
    print("-" * 70)
    test_event_5 = {
        "review_id": str(test_review_id),
        "user_id": initial_review['reviewer_id'],
        "rating": 6
    }
    
    result = handler(test_event_5, None)
    print(f"Status Code: {result['statusCode']}")
    body = json.loads(result['body'])
    print("Response:")
    print(json.dumps(body, indent=2))
    
    if result['statusCode'] == 400:
        print("\n✅ Correctly rejected invalid rating")
    
    # Test 6: Comment too short (should fail)
    print("\n📋 Test 6: Comment too short (should return 400)")
    print("-" * 70)
    test_event_6 = {
        "review_id": str(test_review_id),
        "user_id": initial_review['reviewer_id'],
        "comment": "Short"
    }
    
    result = handler(test_event_6, None)
    print(f"Status Code: {result['statusCode']}")
    body = json.loads(result['body'])
    print("Response:")
    print(json.dumps(body, indent=2))
    
    if result['statusCode'] == 400:
        print("\n✅ Correctly rejected short comment")
    
    # Test 7: Non-existent review (should fail)
    print("\n📋 Test 7: Non-existent review (should return 404)")
    print("-" * 70)
    test_event_7 = {
        "review_id": "99999",
        "user_id": 1,
        "rating": 4
    }
    
    result = handler(test_event_7, None)
    print(f"Status Code: {result['statusCode']}")
    body = json.loads(result['body'])
    print("Response:")
    print(json.dumps(body, indent=2))
    
    if result['statusCode'] == 404:
        print("\n✅ Correctly returned 404 for non-existent review")
    
    # Test 8: Wrong user (should fail with 403)
    print("\n📋 Test 8: Update by different user (should return 403)")
    print("-" * 70)
    test_event_8 = {
        "review_id": str(test_review_id),
        "user_id": 999,  # Different user
        "rating": 4
    }
    
    result = handler(test_event_8, None)
    print(f"Status Code: {result['statusCode']}")
    body = json.loads(result['body'])
    print("Response:")
    print(json.dumps(body, indent=2))
    
    if result['statusCode'] == 403:
        print("\n✅ Correctly rejected unauthorized update")
    
    # Test 9: Empty body (should fail)
    print("\n📋 Test 9: Empty request body (should return 400)")
    print("-" * 70)
    test_event_9 = {
        "review_id": str(test_review_id),
        "user_id": initial_review['reviewer_id']
    }
    
    result = handler(test_event_9, None)
    print(f"Status Code: {result['statusCode']}")
    body = json.loads(result['body'])
    print("Response:")
    print(json.dumps(body, indent=2))
    
    if result['statusCode'] == 400:
        print("\n✅ Correctly rejected empty body")
    
    # Restore original rating
    print("\n📋 Restoring original rating...")
    print("-" * 70)
    restore_event = {
        "review_id": str(test_review_id),
        "user_id": initial_review['reviewer_id'],
        "rating": initial_rating,
        "comment": initial_review['comment']
    }
    
    result = handler(restore_event, None)
    if result['statusCode'] == 200:
        print(f"✅ Restored original rating: {initial_rating} stars")
    
    print("\n" + "=" * 70)
    print("✅ All tests complete!")
    print("=" * 70)

if __name__ == "__main__":
    test_update_review()
