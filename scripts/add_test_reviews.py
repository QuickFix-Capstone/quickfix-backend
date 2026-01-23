#!/usr/bin/env python3
"""
Add test review data to the database for testing get_provider_reviews endpoint.
"""

import sys
sys.path.insert(0, '/Users/ykpfly/Desktop/capstone/quickfix_backend')

from src.db.rds_main import get_connection

def add_test_reviews():
    """Add test reviews and update provider ratings."""
    conn = get_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        cur = conn.cursor()
        
        # Check if we have customers
        print("📋 Checking for customers...")
        cur.execute("SELECT customer_id, CONCAT(first_name, ' ', last_name) as name FROM customers LIMIT 5")
        customers = cur.fetchall()
        
        if not customers:
            print("⚠️  No customers found. Please add customers first.")
            return False
        
        print(f"✅ Found {len(customers)} customers:")
        for c in customers:
            print(f"   - Customer {c['customer_id']}: {c['name']}")
        
        # Check if reviews already exist
        print("\n🔍 Checking for existing reviews...")
        cur.execute("SELECT COUNT(*) as count FROM reviews WHERE reviewee_type = 'provider'")
        existing_count = cur.fetchone()['count']
        
        if existing_count > 0:
            print(f"⚠️  Found {existing_count} existing provider reviews.")
            response = input("Do you want to add more test reviews? (y/n): ")
            if response.lower() != 'y':
                print("❌ Cancelled")
                return False
        
        print("\n📝 Adding test reviews...")
        
        # Reviews for SP-001 (Carter Plumbing)
        reviews_sp001 = [
            (1, 1, 'customer', 'SP-001', 'provider', 5, 'Excellent plumbing service! Very professional and fixed my leak quickly.'),
            (2, 2, 'customer', 'SP-001', 'provider', 4, 'Good work, arrived on time. Would recommend.'),
            (3, 3, 'customer', 'SP-001', 'provider', 5, 'Outstanding service! Carter Plumbing is the best in town.')
        ]
        
        # Reviews for SP-002 (Rogers Electrical)
        reviews_sp002 = [
            (4, 1, 'customer', 'SP-002', 'provider', 3, 'Service was okay, but took longer than expected.'),
            (5, 4, 'customer', 'SP-002', 'provider', 5, 'Great electrician! Fixed my wiring issues perfectly.')
        ]
        
        # Reviews for SP-003 (Chen HVAC Services)
        reviews_sp003 = [
            (6, 2, 'customer', 'SP-003', 'provider', 5, 'Amazing HVAC service! My AC is working perfectly now.'),
            (7, 3, 'customer', 'SP-003', 'provider', 4, 'Very knowledgeable and friendly. Good pricing too.'),
            (8, 5, 'customer', 'SP-003', 'provider', 5, 'Chen HVAC is fantastic! Highly recommend for any heating/cooling needs.')
        ]
        
        all_reviews = reviews_sp001 + reviews_sp002 + reviews_sp003
        
        insert_sql = """
            INSERT INTO reviews (job_id, reviewer_id, reviewer_type, reviewee_id, reviewee_type, rating, comment)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        added_count = 0
        for review in all_reviews:
            try:
                cur.execute(insert_sql, review)
                added_count += 1
            except Exception as e:
                if "Duplicate entry" in str(e):
                    print(f"   ⚠️  Skipping duplicate review for job {review[0]}")
                else:
                    print(f"   ❌ Error adding review: {e}")
        
        conn.commit()
        print(f"✅ Added {added_count} reviews")
        
        # Update provider ratings
        print("\n📊 Updating provider ratings...")
        
        updates = [
            ('SP-001', 14, 3, 4.67),  # 5+4+5=14, 14/3=4.67
            ('SP-002', 8, 2, 4.00),   # 3+5=8, 8/2=4.00
            ('SP-003', 14, 3, 4.67)   # 5+4+5=14, 14/3=4.67
        ]
        
        update_sql = """
            UPDATE service_providers 
            SET 
                total_rating_points = %s,
                total_review_count = %s,
                average_rating = %s
            WHERE provider_id = %s
        """
        
        for provider_id, points, count, avg in updates:
            cur.execute(update_sql, (points, count, avg, provider_id))
            print(f"   ✅ Updated {provider_id}: {avg} avg ({count} reviews)")
        
        conn.commit()
        
        # Verify the data
        print("\n📊 Verification:")
        print("-" * 70)
        
        cur.execute("""
            SELECT 
                provider_id, 
                business_name, 
                average_rating, 
                total_review_count 
            FROM service_providers 
            WHERE provider_id IN ('SP-001', 'SP-002', 'SP-003')
        """)
        
        providers = cur.fetchall()
        for p in providers:
            print(f"   {p['provider_id']}: {p['business_name']}")
            print(f"      Rating: {p['average_rating']} ({p['total_review_count']} reviews)")
        
        print("\n" + "=" * 70)
        print("✅ Test data added successfully!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 70)
    print("Adding Test Review Data")
    print("=" * 70)
    print()
    
    success = add_test_reviews()
    
    if success:
        print("\n💡 Next steps:")
        print("   1. Test the handler: PYTHONPATH=/Users/ykpfly/Desktop/capstone/quickfix_backend python3 lambda/reviews/get_provider_reviews/handler.py")
        print("   2. Or run a specific test for SP-001")
    else:
        print("\n❌ Failed to add test data")
        sys.exit(1)
