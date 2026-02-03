#!/usr/bin/env python3
"""
Run database migration for Budget Change Request feature
"""
import os
import sys

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from src.db.rds_main import get_connection


def run_migration():
    """Run the migration to add budget change request feature"""
    print("🔄 Running database migration: add_budget_change_request_tables")
    print("=" * 80)

    conn = get_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False

    try:
        with conn.cursor() as cur:
            # Step 1: Add budget_change_pending to jobs.status ENUM
            print("\n📝 Step 1: Adding 'budget_change_pending' status to jobs table...")
            sql_alter_jobs = """
                ALTER TABLE jobs
                MODIFY COLUMN status ENUM(
                    'open',
                    'assigned',
                    'in_progress',
                    'budget_change_pending',
                    'completed',
                    'cancelled'
                ) NOT NULL DEFAULT 'open'
            """
            cur.execute(sql_alter_jobs)
            conn.commit()
            print("✅ Jobs status ENUM updated successfully")

            # Verify jobs.status change
            print("\n🔍 Verifying jobs.status ENUM change...")
            cur.execute("""
                SELECT COLUMN_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'jobs'
                  AND COLUMN_NAME = 'status'
            """)
            result = cur.fetchone()
            print(f"✅ Current jobs.status ENUM: {result['COLUMN_TYPE']}")

            if 'budget_change_pending' not in result['COLUMN_TYPE']:
                print("❌ ERROR: budget_change_pending not found in ENUM!")
                return False

            # Step 2: Create job_price_change_requests table
            print("\n📝 Step 2: Creating job_price_change_requests table...")
            sql_create_table = """
                CREATE TABLE IF NOT EXISTS job_price_change_requests (
                    request_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    job_id BIGINT NOT NULL,
                    requested_by_provider_id VARCHAR(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
                    proposed_final_price DECIMAL(10, 2) NOT NULL,
                    reason TEXT NOT NULL,
                    status ENUM('pending', 'accepted', 'rejected', 'cancelled') NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    responded_at TIMESTAMP NULL,

                    CONSTRAINT fk_price_request_job
                        FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
                    CONSTRAINT fk_price_request_provider
                        FOREIGN KEY (requested_by_provider_id) REFERENCES service_providers(provider_id) ON DELETE CASCADE,

                    INDEX idx_job_id (job_id),
                    INDEX idx_job_status (job_id, status),
                    INDEX idx_provider_id (requested_by_provider_id),
                    INDEX idx_created_at (created_at)

                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cur.execute(sql_create_table)
            conn.commit()
            print("✅ job_price_change_requests table created successfully")

            # Verify table creation
            print("\n🔍 Verifying job_price_change_requests table...")
            cur.execute("""
                SELECT TABLE_NAME, ENGINE, TABLE_COLLATION
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'job_price_change_requests'
            """)
            table_info = cur.fetchone()

            if not table_info:
                print("❌ ERROR: job_price_change_requests table not found!")
                return False

            print(f"✅ Table: {table_info['TABLE_NAME']}")
            print(f"   Engine: {table_info['ENGINE']}")
            print(f"   Collation: {table_info['TABLE_COLLATION']}")

            # Verify foreign keys
            print("\n🔍 Verifying foreign key constraints...")
            cur.execute("""
                SELECT
                    CONSTRAINT_NAME,
                    COLUMN_NAME,
                    REFERENCED_TABLE_NAME,
                    REFERENCED_COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'job_price_change_requests'
                  AND REFERENCED_TABLE_NAME IS NOT NULL
            """)
            fks = cur.fetchall()

            if len(fks) != 2:
                print(f"⚠️  WARNING: Expected 2 foreign keys, found {len(fks)}")

            for fk in fks:
                print(f"✅ FK: {fk['CONSTRAINT_NAME']}")
                print(f"   {fk['COLUMN_NAME']} -> {fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}")

            # Verify indexes
            print("\n🔍 Verifying indexes...")
            cur.execute("""
                SELECT
                    INDEX_NAME,
                    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) as COLUMNS,
                    NON_UNIQUE
                FROM INFORMATION_SCHEMA.STATISTICS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'job_price_change_requests'
                GROUP BY INDEX_NAME, NON_UNIQUE
            """)
            indexes = cur.fetchall()

            print(f"✅ Found {len(indexes)} indexes:")
            for idx in indexes:
                idx_type = "UNIQUE" if idx['NON_UNIQUE'] == 0 else "INDEX"
                print(f"   {idx_type}: {idx['INDEX_NAME']} ({idx['COLUMNS']})")

            print("\n" + "=" * 80)
            print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print("\n📋 Summary:")
            print("   ✅ Added budget_change_pending to jobs.status")
            print("   ✅ Created job_price_change_requests table")
            print("   ✅ Set up foreign keys (jobs, service_providers)")
            print("   ✅ Created performance indexes")
            print("\n🎯 Next Steps:")
            print("   1. Deploy Lambda functions for budget change workflows")
            print("   2. Update API Gateway routes")
            print("   3. Run test_budget_change_schema.py to verify")
            print("=" * 80)

            return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
