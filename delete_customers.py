import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.db.rds_main import get_connection

def delete_customers(customer_ids):
    """
    Delete customers by their IDs.
    """
    conn = get_connection()
    if not conn:
        print("❌ Database connection failed")
        return False

    try:
        with conn.cursor() as cur:
            # First, check if the customers exist
            placeholders = ', '.join(['%s'] * len(customer_ids))
            check_sql = f"SELECT customer_id, first_name, last_name, email FROM customers WHERE customer_id IN ({placeholders})"
            cur.execute(check_sql, customer_ids)
            existing_customers = cur.fetchall()

            if not existing_customers:
                print(f"⚠️ No customers found with IDs: {customer_ids}")
                return False

            print(f"📋 Found {len(existing_customers)} customer(s) to delete:")
            for customer in existing_customers:
                print(f"  - ID {customer['customer_id']}: {customer['first_name']} {customer['last_name']} ({customer['email']})")

            # Execute the DELETE
            delete_sql = f"DELETE FROM customers WHERE customer_id IN ({placeholders})"
            cur.execute(delete_sql, customer_ids)
            conn.commit()

            rows_affected = cur.rowcount
            print(f"✅ Successfully deleted {rows_affected} customer(s)")
            return True

    except Exception as e:
        print(f"❌ Error deleting customers: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    customer_ids = [8, 9]
    print(f"🗑️ Attempting to delete customers with IDs: {customer_ids}")
    delete_customers(customer_ids)
