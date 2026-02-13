#!/usr/bin/env python3
"""
Run migration for customer-edit tracking fields on job_applications.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.db.rds_main import get_connection


def _column_exists(cur, table_name: str, column_name: str) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        LIMIT 1
        """,
        (table_name, column_name),
    )
    return cur.fetchone() is not None


def run_migration() -> bool:
    conn = get_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False

    try:
        with conn.cursor() as cur:
            print("🔄 Running migration: customer edit fields for job_applications")

            if not _column_exists(cur, "job_applications", "updated_at"):
                print("📝 Adding job_applications.updated_at ...")
                cur.execute(
                    """
                    ALTER TABLE job_applications
                    ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    """
                )
            else:
                print("⏭️  job_applications.updated_at already exists")

            if not _column_exists(cur, "job_applications", "customer_last_edited_at"):
                print("📝 Adding job_applications.customer_last_edited_at ...")
                cur.execute(
                    """
                    ALTER TABLE job_applications
                    ADD COLUMN customer_last_edited_at TIMESTAMP NULL
                    """
                )
            else:
                print("⏭️  job_applications.customer_last_edited_at already exists")

            conn.commit()

            cur.execute("DESCRIBE job_applications")
            rows = cur.fetchall()
            print("\n📋 job_applications columns:")
            for row in rows:
                if row["Field"] in {"updated_at", "customer_last_edited_at"}:
                    print(f"   ✅ {row['Field']}: {row['Type']} ({row['Null']})")

            print("\n✅ Migration completed successfully")
            return True

    except Exception as exc:
        print(f"❌ Migration failed: {exc}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    ok = run_migration()
    sys.exit(0 if ok else 1)
