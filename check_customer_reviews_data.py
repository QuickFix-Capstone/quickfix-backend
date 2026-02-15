#!/usr/bin/env python3
"""Check what customer review data exists in the database"""

import sys
sys.path.insert(0, '.')

from src.db.rds_main import get_connection

def check_data():
    conn = get_connection()
    if not conn:
        print("❌ Database connection failed")
        return
    
    try:
        with conn.cursor() as cur:
            # Check customers
            print("=" * 70)
            print("CUSTOMERS")
            print("=" * 70)
            cur.execute("SELECT customer_id, first_name, last_name, email FROM customers LIMIT 10")
            customers = cur.fetchall()
            for c in customers:
                print(f"ID: {c['customer_id']}, Name: {c['first_name']} {c['last_name']}, Email: {c['email']}")
            
            # Check customer_provider_reviews
            print("\n" + "=" * 70)
            print("CUSTOMER_PROVIDER_REVIEWS")
            print("=" * 70)
            cur.execute("""
                SELECT 
                    r.review_id,
                    r.customer_id,
                    r.provider_id,
                    r.job_id,
                    r.rating,
                    r.comment,
                    c.first_name,
                    c.last_name
                FROM customer_provider_reviews r
                LEFT JOIN customers c ON r.customer_id = c.customer_id
                LIMIT 10
            """)
            reviews = cur.fetchall()
            
            if not reviews:
                print("No reviews found in customer_provider_reviews table")
            else:
                for r in reviews:
                    print(f"Review ID: {r['review_id']}, Customer: {r['first_name']} {r['last_name']} (ID: {r['customer_id']}), Provider ID: {r['provider_id']}, Job ID: {r['job_id']}, Rating: {r['rating']}")
                    print(f"  Comment: {r['comment'][:50]}...")
            
            # Count reviews per customer
            print("\n" + "=" * 70)
            print("REVIEWS COUNT PER CUSTOMER")
            print("=" * 70)
            cur.execute("""
                SELECT 
                    c.customer_id,
                    c.first_name,
                    c.last_name,
                    COUNT(r.review_id) as review_count
                FROM customers c
                LEFT JOIN customer_provider_reviews r ON c.customer_id = r.customer_id
                GROUP BY c.customer_id, c.first_name, c.last_name
                HAVING review_count > 0
                ORDER BY review_count DESC
            """)
            counts = cur.fetchall()
            
            if not counts:
                print("No customers have written reviews yet")
            else:
                for row in counts:
                    print(f"Customer {row['customer_id']} ({row['first_name']} {row['last_name']}): {row['review_count']} reviews")
    
    finally:
        conn.close()

if __name__ == "__main__":
    check_data()
