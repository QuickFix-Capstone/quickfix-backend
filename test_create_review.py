"""
Test script for create_review Lambda function
"""
import json
import os
import sys

# Add the lambda function path to sys.path
lambda_path = os.path.join(os.path.dirname(__file__), 'lambda', 'reviews', 'create_review')
sys.path.insert(0, lambda_path)

import handler as review_handler
from src.db.rds_main import get_connection


def setup_test_data():
    """Create test job and set it to completed status"""
    conn = get_connection()
    if not conn:
        print("❌ Database connection failed")
        return None, None, None

    try:
        with conn.cursor() as cur:
            # Find or create a completed job
            cur.execute("""
                SELECT job_id, customer_id FROM jobs
                WHERE status = 'completed'
                LIMIT 1
            """)
            job = cur.fetchone()

            if job:
                job_id = job['job_id']
                customer_id = job['customer_id']
                print(f"✓ Found existing completed job: job_id={job_id}")
            else:
                # If no completed job exists, find an open job and complete it for testing
                cur.execute("""
                    SELECT job_id, customer_id FROM jobs
                    WHERE status = 'open'
                    LIMIT 1
                """)
                job = cur.fetchone()

                if not job:
                    print("❌ No jobs found in database")
                    return None, None, None

                job_id = job['job_id']
                customer_id = job['customer_id']

                # Mark it as completed for testing
                cur.execute("""
                    UPDATE jobs
                    SET status = 'completed'
                    WHERE job_id = %s
                """, (job_id,))
                conn.commit()
                print(f"✓ Set job {job_id} to completed status for testing")

            # Get a provider_id
            cur.execute("SELECT provider_id FROM service_providers LIMIT 1")
            provider = cur.fetchone()

            if not provider:
                print("❌ No service providers found in database")
                return None, None, None

            provider_id = provider['provider_id']

            return job_id, customer_id, provider_id

    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        return None, None, None
    finally:
        conn.close()


def test_create_review():
    """Test the create_review Lambda function"""
    print("=" * 60)
    print("Testing create_review Lambda Function")
    print("=" * 60)

    # Setup test data
    job_id, customer_id, provider_id = setup_test_data()

    if not all([job_id, customer_id, provider_id]):
        print("\n❌ Failed to setup test data. Cannot proceed with test.")
        return

    print(f"\nTest Data:")
    print(f"  - Job ID: {job_id}")
    print(f"  - Customer ID: {customer_id}")
    print(f"  - Provider ID: {provider_id}")

    # Test 1: Create a valid review
    print("\n" + "-" * 60)
    print("Test 1: Create a valid customer review")
    print("-" * 60)

    test_event = {
        "body": json.dumps({
            "job_id": job_id,
            "reviewer_id": customer_id,
            "reviewer_type": "customer",
            "reviewee_id": provider_id,
            "reviewee_type": "provider",
            "rating": 5,
            "comment": "Excellent service! Very professional and completed the job on time. Would definitely hire again."
        })
    }

    result = review_handler.handler(test_event, None)
    response_body = json.loads(result["body"])

    print(f"Status Code: {result['statusCode']}")
    print(f"Response: {json.dumps(response_body, indent=2)}")

    if result['statusCode'] == 201:
        print("✅ Test 1 PASSED: Review created successfully")
        review_id = response_body.get('review', {}).get('review_id')
    else:
        print("❌ Test 1 FAILED")
        review_id = None

    # Test 2: Try to create duplicate review (should fail)
    print("\n" + "-" * 60)
    print("Test 2: Try to create duplicate review (should return 409)")
    print("-" * 60)

    result2 = review_handler.handler(test_event, None)
    response_body2 = json.loads(result2["body"])

    print(f"Status Code: {result2['statusCode']}")
    print(f"Response: {json.dumps(response_body2, indent=2)}")

    if result2['statusCode'] == 409:
        print("✅ Test 2 PASSED: Duplicate review rejected")
    else:
        print("❌ Test 2 FAILED: Should have returned 409 Conflict")

    # Test 3: Invalid rating (out of range)
    print("\n" + "-" * 60)
    print("Test 3: Invalid rating (should return 400)")
    print("-" * 60)

    test_event_invalid = {
        "body": json.dumps({
            "job_id": job_id,
            "reviewer_id": customer_id,
            "reviewer_type": "customer",
            "reviewee_id": provider_id,
            "reviewee_type": "provider",
            "rating": 6,  # Invalid: out of range
            "comment": "This rating is out of range and should be rejected."
        })
    }

    result3 = review_handler.handler(test_event_invalid, None)
    response_body3 = json.loads(result3["body"])

    print(f"Status Code: {result3['statusCode']}")
    print(f"Response: {json.dumps(response_body3, indent=2)}")

    if result3['statusCode'] == 400:
        print("✅ Test 3 PASSED: Invalid rating rejected")
    else:
        print("❌ Test 3 FAILED: Should have returned 400 Bad Request")

    # Test 4: Comment too short
    print("\n" + "-" * 60)
    print("Test 4: Comment too short (should return 400)")
    print("-" * 60)

    test_event_short = {
        "body": json.dumps({
            "job_id": job_id,
            "reviewer_id": customer_id,
            "reviewer_type": "customer",
            "reviewee_id": provider_id,
            "reviewee_type": "provider",
            "rating": 4,
            "comment": "Too short"  # Less than 10 characters
        })
    }

    result4 = review_handler.handler(test_event_short, None)
    response_body4 = json.loads(result4["body"])

    print(f"Status Code: {result4['statusCode']}")
    print(f"Response: {json.dumps(response_body4, indent=2)}")

    if result4['statusCode'] == 400:
        print("✅ Test 4 PASSED: Short comment rejected")
    else:
        print("❌ Test 4 FAILED: Should have returned 400 Bad Request")

    # Cleanup: Delete test review
    if review_id:
        print("\n" + "-" * 60)
        print("Cleanup: Deleting test review")
        print("-" * 60)

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM reviews WHERE review_id = %s", (review_id,))
                conn.commit()
                print(f"✅ Deleted test review (ID: {review_id})")
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
        finally:
            conn.close()

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    test_create_review()
