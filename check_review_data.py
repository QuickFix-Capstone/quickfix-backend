#!/usr/bin/env python3
"""
Quick script to check review data for specific jobs
"""
import sys
sys.path.insert(0, '/Users/ykpfly/Desktop/capstone/quickfix_backend')

from src.db.rds_main import get_connection

def check_reviews():
    conn = get_connection()
    if not conn:
        print("❌ Database connection failed")
        return
    
    try:
        with conn.cursor() as cur:
            # Check reviews for job 1 and 4
            sql = """
                SELECT 
                    r.review_id,
                    r.job_id,
                    r.reviewer_id,
                    r.reviewer_type,
                    r.reviewee_id,
                    r.reviewee_type,
                    r.rating,
                    r.comment
                FROM reviews r
                WHERE r.job_id IN (1, 4)
                ORDER BY r.job_id, r.review_id
            """
            cur.execute(sql)
            reviews = cur.fetchall()
            
            print("=" * 70)
            print("Review Data for Jobs 1 and 4")
            print("=" * 70)
            
            for review in reviews:
                print(f"\nReview ID: {review['review_id']}")
                print(f"  Job ID: {review['job_id']}")
                print(f"  Reviewer: {review['reviewer_id']} ({review['reviewer_type']})")
                print(f"  Reviewee: {review['reviewee_id']} ({review['reviewee_type']})")
                print(f"  Rating: {review['rating']}")
                print(f"  Comment: {review['comment'][:50]}...")
            
            print("\n" + "=" * 70)
            print(f"Total reviews found: {len(reviews)}")
            print("=" * 70)
            
    finally:
        conn.close()

if __name__ == "__main__":
    check_reviews()
