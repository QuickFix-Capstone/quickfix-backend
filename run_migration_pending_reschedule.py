"""
Run database migration for pending_reschedule status
"""
import os
import sys

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from src.db.rds_main import get_connection

def run_migration():
    """Run the migration to add pending_reschedule status"""
    print("🔄 Running database migration: add_pending_reschedule_status")
    print("=" * 60)
    
    conn = get_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        with conn.cursor() as cur:
            # Add pending_reschedule to the status ENUM
            print("\n📝 Altering bookings table to add 'pending_reschedule' status...")
            sql = """
                ALTER TABLE bookings 
                MODIFY COLUMN status ENUM(
                    'pending',
                    'pending_confirmation',
                    'confirmed',
                    'pending_reschedule',
                    'in_progress',
                    'completed',
                    'cancelled'
                ) NOT NULL DEFAULT 'pending'
            """
            cur.execute(sql)
            conn.commit()
            print("✅ Status ENUM updated successfully")
            
            # Verify the change
            print("\n🔍 Verifying the change...")
            cur.execute("""
                SELECT COLUMN_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'bookings' 
                  AND COLUMN_NAME = 'status'
            """)
            result = cur.fetchone()
            print(f"✅ Current status ENUM: {result['COLUMN_TYPE']}")
            
            print("\n✅ Migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
