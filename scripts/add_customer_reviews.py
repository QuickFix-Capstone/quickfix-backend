#!/usr/bin/env python3
"""
Add test customer review data (providers reviewing customers).
This is the opposite direction from the provider reviews we added earlier.
"""

import sys
sys.path.insert(0, '/Users/ykpfly/Desktop/capstone/quickfix_backend')

from src.db.rds_main import get_connection

def add_customer_reviews():
    """Add test reviews where providers review customers."""
    conn = get_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        cur = conn.cursor()
        
        # Check existing customer reviews
        print("🔍 Checking for existing customer reviews...")
        cur.execute("SELECT COUNT(*) as count FROM reviews WHERE reviewee_type = 'customer'")
        existing_count = cur.fetchone()['count']
        
        if existing_count > 0:
            print(f"⚠️  Found {existing_count} existing customer reviews.")
            response = input("Do you want to add more test reviews? (y/n): ")
            if response.lower() != 'y':
                print("❌ Cancelled")
                return False
        
        print("\n📝 Adding test customer reviews (providers reviewing customers)...")
        
        # Reviews where providers review customers
        # Format: (job_id, reviewer_id, reviewer_type, reviewee_id, reviewee_type, rating, comment)
        
        # Customer 1 (Test User) - reviewed by providers
        reviews_customer_1 = [
            (10, 'SP-001', 'provider', 1, 'customer', 5, 'Great customer! Very clear about requirements and paid promptly.'),
            (11, 'SP-002', 'provider', 1, 'customer', 4, 'Good communication, would work with again.'),
        ]
        
        # Customer 2 (KunPeng Yang) - reviewed by providers
        reviews_customer_2 = [
            (12, 'SP-001', 'provider', 2, 'customer', 5, 'Excellent customer! Very professional and respectful.'),
            (13, 'SP-003', 'provider', 2, 'customer', 5, 'Perfect client. Clear expectations and friendly.'),
            (14, 'SP-004', 'provider', 2, 'customer', 4, 'Nice customer, easy to work with.'),
        ]
        
        # Customer 3 (Ajay Persaud) - reviewed by providers
        reviews_customer_3 = [
            (15, 'SP-002', 'provider', 3, 'customer', 3, 'Customer was okay but kept changing requirements.'),
            (16, 'SP-005', 'provider', 3, 'customer', 4, 'Good customer overall, minor communication issues.'),
        ]
        
        all_reviews = reviews_customer_1 + reviews_customer_2 + reviews_customer_3
        
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
                elif "foreign key constraint" in str(e).lower():
                    print(f"   ⚠️  Skipping review for job {review[0]} (job doesn't exist)")
                else:
                    print(f"   ❌ Error adding review: {e}")
        
        conn.commit()
        print(f"✅ Added {added_count} customer reviews")
        
        # Update customer ratings
        print("\n📊 Updating customer ratings...")
        
        # Customer 1: 2 reviews, ratings: 5, 4 = total 9 points, avg 4.50
        # Customer 2: 3 reviews, ratings: 5, 5, 4 = total 14 points, avg 4.67
        # Customer 3: 2 reviews, ratings: 3, 4 = total 7 points, avg 3.50
        
        updates = [
            (1, 9, 2, 4.50),   # Customer 1
            (2, 14, 3, 4.67),  # Customer 2
            (3, 7, 2, 3.50),   # Customer 3
        ]
        
        update_sql = """
            UPDATE customers 
            SET 
                total_rating_points = %s,
                total_review_count = %s,
                average_rating = %s
            WHERE customer_id = %s
        """
        
        for customer_id, points, count, avg in updates:
            cur.execute(update_sql, (points, count, avg, customer_id))
            print(f"   ✅ Updated Customer {customer_id}: {avg} avg ({count} reviews)")
        
        conn.commit()
        
        # Verify the data
        print("\n📊 Verification:")
        print("-" * 70)
        
        cur.execute("""
            SELECT 
                customer_id, 
                CONCAT(first_name, ' ', last_name) as name,
                average_rating, 
                total_review_count 
            FROM customers 
            WHERE customer_id IN (1, 2, 3)
        """)
        
        customers = cur.fetchall()
        for c in customers:
            print(f"   Customer {c['customer_id']}: {c['name']}")
            print(f"      Rating: {c['average_rating']} ({c['total_review_count']} reviews)")
        
        # Show sample reviews
        print("\n📋 Sample Customer Reviews:")
        print("-" * 70)
        cur.execute("""
            SELECT 
                r.review_id,
                r.reviewee_id,
                CONCAT(c.first_name, ' ', c.last_name) as customer_name,
                sp.business_name as reviewer_name,
                r.rating,
                r.comment
            FROM reviews r
            JOIN customers c ON r.reviewee_id = c.customer_id
            JOIN service_providers sp ON r.reviewer_id = sp.provider_id
            WHERE r.reviewee_type = 'customer'
            LIMIT 3
        """)
        
        sample_reviews = cur.fetchall()
        for rev in sample_reviews:
            print(f"   {rev['reviewer_name']} → {rev['customer_name']}: {rev['rating']}⭐")
            print(f"      \"{rev['comment'][:60]}...\"")
        
        print("\n" + "=" * 70)
        print("✅ Customer review test data added successfully!")
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
    print("Adding Test Customer Review Data")
    print("(Providers reviewing customers)")
    print("=" * 70)
    print()
    
    success = add_customer_reviews()
    
    if success:
        print("\n💡 Next steps:")
        print("   1. Implement get_customer_reviews handler")
        print("   2. Test locally with Customer 2 (best rating: 4.67)")
        print("   3. Deploy to AWS")
    else:
        print("\n❌ Failed to add test data")
        sys.exit(1)
