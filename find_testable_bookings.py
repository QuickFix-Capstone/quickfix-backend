"""
Quick script to find bookings for customer that are in testable status
"""
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from src.db.rds_main import get_connection

CUSTOMER_ID = 14
CUSTOMER_COGNITO_SUB = "117b75e0-f0d1-705b-736a-49b964f8b11c"

conn = get_connection()
if conn:
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT booking_id, status, scheduled_date, scheduled_time, 
                       service_category, service_description
                FROM bookings
                WHERE customer_id = %s
                ORDER BY created_at DESC
                LIMIT 10
            """, (CUSTOMER_ID,))
            
            bookings = cur.fetchall()
            
            print(f"\n📋 Bookings for Customer #{CUSTOMER_ID} (KunPeng Yang)")
            print("=" * 80)
            
            if not bookings:
                print("No bookings found")
            else:
                for booking in bookings:
                    status_emoji = {
                        'pending': '⏳',
                        'pending_confirmation': '📧',
                        'confirmed': '✅',
                        'pending_reschedule': '📅',
                        'in_progress': '🔧',
                        'completed': '✔️',
                        'cancelled': '❌'
                    }.get(booking['status'], '❓')
                    
                    print(f"\n{status_emoji} Booking #{booking['booking_id']}")
                    print(f"   Status: {booking['status']}")
                    print(f"   Service: {booking['service_category']} - {booking['service_description']}")
                    print(f"   Scheduled: {booking['scheduled_date']} at {booking['scheduled_time']}")
                    
                    # Indicate which are testable
                    testable_statuses = ['pending', 'pending_confirmation', 'confirmed', 'pending_reschedule']
                    if booking['status'] in testable_statuses:
                        print(f"   ✨ TESTABLE - Can use for update_booking tests")
            
            print("\n" + "=" * 80)
            
    finally:
        conn.close()
else:
    print("Failed to connect to database")
