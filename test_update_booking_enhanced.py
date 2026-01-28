"""
Test script for enhanced update_booking handler
Tests reschedule functionality, status transitions, and field validation
"""
import json
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import handler using sys.path manipulation to avoid 'lambda' keyword issue
sys.path.insert(0, os.path.join(current_dir, 'lambda', 'bookings', 'update_booking'))
import handler as update_booking_handler


def create_test_event(booking_id, body_data, cognito_sub="117b75e0-f0d1-705b-736a-49b964f8b11c"):
    """Create a test event for the handler"""
    return {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": cognito_sub
                    }
                }
            }
        },
        "pathParameters": {
            "booking_id": str(booking_id)
        },
        "body": json.dumps(body_data)
    }


def print_result(test_name, result):
    """Print test result in a readable format"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")
    print(f"Status Code: {result['statusCode']}")
    body = json.loads(result['body'])
    print(f"Response: {json.dumps(body, indent=2)}")
    print(f"{'='*60}\n")


def main():
    print("🧪 Testing Enhanced Update Booking Handler")
    print("=" * 60)
    
    # Test 1: Cancel booking (existing functionality)
    print("\n📋 Test 1: Cancel Booking")
    event1 = create_test_event(84, {
        "status": "cancelled",
        "notes": "No longer needed"
    })
    result1 = update_booking_handler.handler(event1, None)
    print_result("Cancel Booking", result1)
    
    # Test 2: Reschedule booking (new date/time)
    print("\n📋 Test 2: Reschedule Booking")
    future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    event2 = create_test_event(84, {
        "scheduled_date": future_date,
        "scheduled_time": "14:30:00",
        "notes": "Rescheduled to next week"
    })
    result2 = update_booking_handler.handler(event2, None)
    print_result("Reschedule Booking", result2)
    
    # Test 3: Try to reschedule to past date (should fail)
    print("\n📋 Test 3: Reschedule to Past Date (Should Fail)")
    past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    event3 = create_test_event(84, {
        "scheduled_date": past_date,
        "scheduled_time": "10:00:00"
    })
    result3 = update_booking_handler.handler(event3, None)
    print_result("Reschedule to Past (Should Fail)", result3)
    
    # Test 4: Update address
    print("\n📋 Test 4: Update Service Address")
    event4 = create_test_event(84, {
        "service_address": "456 New Street",
        "service_city": "Toronto",
        "service_state": "ON",
        "service_postal_code": "M5H 2N2"
    })
    result4 = update_booking_handler.handler(event4, None)
    print_result("Update Address", result4)
    
    # Test 5: Change status to pending_reschedule
    print("\n📋 Test 5: Change Status to Pending Reschedule")
    event5 = create_test_event(84, {
        "status": "pending_reschedule",
        "notes": "Customer needs more time to decide on date"
    })
    result5 = update_booking_handler.handler(event5, None)
    print_result("Change to Pending Reschedule", result5)
    
    # Test 6: Try to update invalid field for current status (should fail)
    print("\n📋 Test 6: Update Invalid Field (Should Fail)")
    event6 = create_test_event(84, {
        "estimated_price": 200.00  # Not in updatable_fields
    })
    result6 = update_booking_handler.handler(event6, None)
    print_result("Update Invalid Field (Should Fail)", result6)
    
    print("\n✅ All tests completed!")
    print("\nNote: Some tests may fail if:")
    print("  - Booking #84 doesn't exist")
    print("  - Booking status doesn't allow the transition")
    print("  - Database schema hasn't been updated with pending_reschedule")


if __name__ == "__main__":
    main()
