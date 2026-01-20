#!/usr/bin/env python3
"""
Test script for delete_review Lambda function.
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
    "/Users/ykpfly/Desktop/capstone/quickfix_backend/lambda/reviews/delete_review/handler.py"
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


def create_test_review():
    """Create a test review for deletion."""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            # Create a test review (using job_id=3 to avoid unique constraint)
            cur.execute(
                """
                INSERT INTO reviews 
                (job_id, reviewer_id, reviewer_type, reviewee_id, reviewee_type, rating, comment)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (3, 1, 'customer', 0, 'provider', 3, 'Test review for deletion - will be removed shortly.')
            )
            conn.commit()
            review_id = cur.lastrowid
            
            # Update provider rating
            cur.execute(
                """
                UPDATE service_providers
                SET 
                    total_rating_points = total_rating_points + 3,
                    total_review_count = total_review_count + 1,
                    average_rating = (total_rating_points + 3) / (total_review_count + 1)
                WHERE provider_id = 0
                """
            )
            conn.commit()
            
            return review_id
    finally:
        conn.close()


def test_delete_review():
    print("=" * 70)
    print("Testing DELETE /reviews/{review_id} with Database Data")
    print("=" * 70)
    
    # Create a test review
    print("\n📋 Setup: Creating test review...")
    print("-" * 70)
    test_review_id = create_test_review()
    if not test_review_id:
        print("❌ Failed to create test review!")
        return
    
    print(f"✅ Created test review #{test_review_id}")
    
    # Check provider rating before deletion
    provider_rating_before = get_provider_rating(0)
    if provider_rating_before:
        print(f"\nProvider Rating Before Deletion:")
        print(f"  Average: {provider_rating_before['average_rating']}")
        print(f"  Total Points: {provider_rating_before['total_rating_points']}")
        print(f"  Total Count: {provider_rating_before['total_review_count']}")
    
    # Test 1: Delete the test review
    print(f"\n📋 Test 1: Delete review #{test_review_id}")
    print("-" * 70)
    test_event_1 = {
        "review_id": str(test_review_id),
        "user_id": 1,
        "user_type": "customer"
    }
    
    result = handler(test_event_1, None)
    print(f"Status Code: {result['statusCode']}")
    body = json.loads(result['body'])
    print("Response:")
    print(json.dumps(body, indent=2))
    
    if result['statusCode'] == 200:
        print("\n✅ Review deleted successfully")
        
        # Verify rating recalculation
        provider_rating_after = get_provider_rating(0)
        if provider_rating_after:
            print(f"\nProvider Rating After Deletion:")
            print(f"  Average: {provider_rating_after['average_rating']}")
            print(f"  Total Points: {provider_rating_after['total_rating_points']}")
            print(f"  Total Count: {provider_rating_after['total_review_count']}")
            
            # Calculate expected values
            expected_points = provider_rating_before['total_rating_points'] - 3
            expected_count = provider_rating_before['total_review_count'] - 1
            print(f"\n  Expected points: {expected_points}")
            print(f"  Expected count: {expected_count}")
            
            if (provider_rating_after['total_rating_points'] == expected_points and
                provider_rating_after['total_review_count'] == expected_count):
                print("  ✅ Rating recalculation correct!")
            else:
                print("  ❌ Rating recalculation mismatch!")
        
        # Verify review is actually deleted
        deleted_review = get_review(test_review_id)
        if deleted_review is None:
            print(f"\n✅ Review #{test_review_id} confirmed deleted from database")
        else:
            print(f"\n❌ Review #{test_review_id} still exists in database!")
    else:
        print(f"\n❌ Delete failed: {body.get('message')}")
    
    # Test 2: Try to delete non-existent review
    print("\n📋 Test 2: Delete non-existent review (should return 404)")
    print("-" * 70)
    test_event_2 = {
        "review_id": "99999",
        "user_id": 1
    }
    
    result = handler(test_event_2, None)
    print(f"Status Code: {result['statusCode']}")
    body = json.loads(result['body'])
    print("Response:")
    print(json.dumps(body, indent=2))
    
    if result['statusCode'] == 404:
        print("\n✅ Correctly returned 404 for non-existent review")
    
    # Test 3: Try to delete someone else's review
    print("\n📋 Test 3: Delete someone else's review (should return 403)")
    print("-" * 70)
    test_event_3 = {
        "review_id": "4",  # Belongs to customer_id = 2
        "user_id": 999  # Different user
    }
    
    result = handler(test_event_3, None)
    print(f"Status Code: {result['statusCode']}")
    body = json.loads(result['body'])
    print("Response:")
    print(json.dumps(body, indent=2))
    
    if result['statusCode'] == 403:
        print("\n✅ Correctly rejected unauthorized deletion")
    
    # Test 4: Try to delete already deleted review
    print(f"\n📋 Test 4: Delete already deleted review (should return 404)")
    print("-" * 70)
    test_event_4 = {
        "review_id": str(test_review_id),
        "user_id": 1
    }
    
    result = handler(test_event_4, None)
    print(f"Status Code: {result['statusCode']}")
    body = json.loads(result['body'])
    print("Response:")
    print(json.dumps(body, indent=2))
    
    if result['statusCode'] == 404:
        print("\n✅ Correctly returned 404 for already deleted review")
    
    print("\n" + "=" * 70)
    print("✅ All tests complete!")
    print("=" * 70)

if __name__ == "__main__":
    test_delete_review()
