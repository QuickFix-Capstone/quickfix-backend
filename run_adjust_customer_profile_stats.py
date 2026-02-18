#!/usr/bin/env python3
"""
Adjust customer_profile_stats table - Remove avg_rating column
Since customers table already has average_rating, we don't need to duplicate it
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.db.rds_main import get_connection

def run_adjustment():
    """Remove avg_rating from customer_profile_stats table."""
    
    print("\n" + "="*80)
    print("🔧 Adjusting customer_profile_stats table")
    print("="*80)
    print("Reason: customers table already has average_rating column")
    print("Action: Removing duplicate avg_rating from customer_profile_stats")
    print("="*80)
    
    print("\n🔍 Connecting to database...")
    conn = get_connection()
    
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        with conn.cursor() as cur:
            # Check if avg_rating exists in customer_profile_stats
            cur.execute("""
                SELECT COUNT(*) as count FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'customer_profile_stats'
                  AND COLUMN_NAME = 'avg_rating'
            """)
            exists = cur.fetchone()['count'] > 0
            
            if exists:
                print("\n📝 Removing avg_rating column from customer_profile_stats...")
                cur.execute("ALTER TABLE customer_profile_stats DROP COLUMN avg_rating")
                conn.commit()
                print("✅ avg_rating column removed")
            else:
                print("\n⚠️  avg_rating column doesn't exist in customer_profile_stats, skipping")
            
            # Verify customers table has average_rating
            print("\n🔍 Verifying customers table has rating columns...")
            cur.execute("""
                SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'customers'
                  AND COLUMN_NAME IN ('average_rating', 'total_rating_points', 'total_review_count')
                ORDER BY COLUMN_NAME
            """)
            customer_cols = cur.fetchall()
            
            if customer_cols:
                print("\n📋 Customers table rating columns:")
                print("-" * 80)
                for col in customer_cols:
                    print(f"  ✅ {col['COLUMN_NAME']:25} {col['COLUMN_TYPE']:20} - {col['COLUMN_COMMENT']}")
                print("-" * 80)
            else:
                print("⚠️  Warning: customers table doesn't have rating columns!")
            
            # Show final customer_profile_stats structure
            print("\n📋 Final customer_profile_stats structure:")
            print("-" * 80)
            cur.execute("DESCRIBE customer_profile_stats")
            columns = cur.fetchall()
            for col in columns:
                print(f"  {col['Field']:30} {col['Type']:20} {col['Null']:5} {col['Key']:5}")
            print("-" * 80)
            
            print("\n✅ Adjustment completed successfully!")
            print("\nNote: Use customers.average_rating for customer ratings in queries")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Adjustment failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = run_adjustment()
    sys.exit(0 if success else 1)
