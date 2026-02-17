#!/usr/bin/env python3
"""
Run database migrations for Customer Public Profile - Phase 1
Includes:
- Customer profile fields (display_name, profile_visibility)
- Customer profile stats table
- Review visibility flag
- Provider-customer interactions table
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.db.rds_main import get_connection

def run_migration_1_1(conn):
    """Migration 1.1: Add Customer Profile Fields"""
    print("\n" + "="*80)
    print("📝 Migration 1.1: Adding customer profile fields...")
    print("="*80)
    
    # Check if display_name exists
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) as count FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'customers'
              AND COLUMN_NAME = 'display_name'
        """)
        exists = cur.fetchone()['count'] > 0
    
    if not exists:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    ALTER TABLE customers
                    ADD COLUMN display_name VARCHAR(100) NULL 
                    COMMENT 'Public display name'
                """)
                conn.commit()
                print("✅ Added display_name column")
        except Exception as e:
            print(f"⚠️  Error adding display_name: {e}")
    else:
        print("⚠️  display_name column already exists, skipping")
    
    # Check if profile_visibility exists
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) as count FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'customers'
              AND COLUMN_NAME = 'profile_visibility'
        """)
        exists = cur.fetchone()['count'] > 0
    
    if not exists:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    ALTER TABLE customers
                    ADD COLUMN profile_visibility ENUM('public', 'restricted', 'private') 
                    NOT NULL DEFAULT 'restricted' 
                    COMMENT 'Who can view profile: public=all providers, restricted=interacted only, private=hidden'
                """)
                conn.commit()
                print("✅ Added profile_visibility column")
        except Exception as e:
            print(f"⚠️  Error adding profile_visibility: {e}")
    else:
        print("⚠️  profile_visibility column already exists, skipping")
    
    # Check if index exists
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) as count FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'customers'
              AND INDEX_NAME = 'idx_profile_visibility'
        """)
        exists = cur.fetchone()['count'] > 0
    
    if not exists:
        try:
            with conn.cursor() as cur:
                cur.execute("ALTER TABLE customers ADD INDEX idx_profile_visibility (profile_visibility)")
                conn.commit()
                print("✅ Added profile_visibility index")
        except Exception as e:
            print(f"⚠️  Error adding index: {e}")
    else:
        print("⚠️  Index already exists, skipping")
    
    # Verify
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'customers'
              AND COLUMN_NAME IN ('display_name', 'profile_visibility')
            ORDER BY ORDINAL_POSITION
        """)
        columns = cur.fetchall()
        
        print("\n📋 Verified Columns:")
        print("-" * 80)
        for col in columns:
            print(f"  {col['COLUMN_NAME']:25} {col['COLUMN_TYPE']:30} Default: {col['COLUMN_DEFAULT'] or 'NULL'}")
        print("-" * 80)

def run_migration_1_2(conn):
    """Migration 1.2: Create Customer Profile Stats Table"""
    print("\n" + "="*80)
    print("📝 Migration 1.2: Creating customer_profile_stats table...")
    print("="*80)
    
    migration_sql = """
    CREATE TABLE IF NOT EXISTS customer_profile_stats (
        customer_id BIGINT PRIMARY KEY,
        avg_rating DECIMAL(3,2) NULL COMMENT 'Average rating from provider reviews',
        review_count INT NOT NULL DEFAULT 0,
        jobs_posted_6mo INT NOT NULL DEFAULT 0,
        jobs_completed INT NOT NULL DEFAULT 0,
        jobs_cancelled INT NOT NULL DEFAULT 0,
        completion_rate DECIMAL(5,2) NULL COMMENT 'Percentage of completed jobs',
        cancellation_rate DECIMAL(5,2) NULL COMMENT 'Percentage of cancelled jobs',
        avg_response_time_minutes INT NULL COMMENT 'Average message response time',
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        CONSTRAINT fk_stats_customer 
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
        
        INDEX idx_last_updated (last_updated)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    COMMENT='Cached customer profile statistics for performance optimization'
    """
    
    try:
        with conn.cursor() as cur:
            cur.execute(migration_sql)
            conn.commit()
            print("✅ customer_profile_stats table created")
            
            # Verify
            cur.execute("DESCRIBE customer_profile_stats")
            columns = cur.fetchall()
            
            print("\n📋 Table Structure:")
            print("-" * 80)
            for col in columns:
                print(f"  {col['Field']:30} {col['Type']:20} {col['Null']:5} {col['Key']:5}")
            print("-" * 80)
            
    except Exception as e:
        print(f"❌ Failed to create customer_profile_stats table: {e}")
        raise

def run_migration_1_3(conn):
    """Migration 1.3: Add Review Visibility Flag"""
    print("\n" + "="*80)
    print("📝 Migration 1.3: Adding review visibility flag...")
    print("="*80)
    
    # Add is_visible to provider_customer_reviews (reviews ABOUT customers)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) as count FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'provider_customer_reviews'
              AND COLUMN_NAME = 'is_visible'
        """)
        exists = cur.fetchone()['count'] > 0
    
    if not exists:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    ALTER TABLE provider_customer_reviews
                    ADD COLUMN is_visible BOOLEAN NOT NULL DEFAULT TRUE 
                    COMMENT 'Whether review is publicly visible on customer profile'
                """)
                conn.commit()
                print("✅ Added is_visible column to provider_customer_reviews")
        except Exception as e:
            print(f"⚠️  Error adding is_visible to provider_customer_reviews: {e}")
    else:
        print("⚠️  is_visible column already exists in provider_customer_reviews, skipping")
    
    # Add index for customer queries
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) as count FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'provider_customer_reviews'
              AND INDEX_NAME = 'idx_customer_visible'
        """)
        exists = cur.fetchone()['count'] > 0
    
    if not exists:
        try:
            with conn.cursor() as cur:
                cur.execute("ALTER TABLE provider_customer_reviews ADD INDEX idx_customer_visible (customer_id, is_visible)")
                conn.commit()
                print("✅ Added idx_customer_visible index to provider_customer_reviews")
        except Exception as e:
            print(f"⚠️  Error adding index: {e}")
    else:
        print("⚠️  idx_customer_visible already exists, skipping")
    
    # Verify
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'provider_customer_reviews'
              AND COLUMN_NAME = 'is_visible'
        """)
        column = cur.fetchone()
        
        if column:
            print("\n📋 Verified Column:")
            print("-" * 80)
            print(f"  {column['COLUMN_NAME']:20} {column['COLUMN_TYPE']:20} Default: {column['COLUMN_DEFAULT']}")
            print("-" * 80)
    
    # Verify
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'reviews'
              AND COLUMN_NAME = 'is_visible'
        """)
        column = cur.fetchone()
        
        if column:
            print("\n📋 Verified Column:")
            print("-" * 80)
            print(f"  {column['COLUMN_NAME']:20} {column['COLUMN_TYPE']:20} Default: {column['COLUMN_DEFAULT']}")
            print("-" * 80)

def run_migration_1_4(conn):
    """Migration 1.4: Create Provider-Customer Interactions Table"""
    print("\n" + "="*80)
    print("📝 Migration 1.4: Creating provider_customer_interactions table...")
    print("="*80)
    
    # First, check the actual type of provider_id in service_providers
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'service_providers'
              AND COLUMN_NAME = 'provider_id'
        """)
        result = cur.fetchone()
        provider_id_type = result['COLUMN_TYPE'] if result else 'bigint'
        print(f"📋 Detected service_providers.provider_id type: {provider_id_type}")
    
    # Create table with matching type (without foreign keys first to avoid issues)
    migration_sql = f"""
    CREATE TABLE IF NOT EXISTS provider_customer_interactions (
        interaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
        provider_id {provider_id_type} NOT NULL COMMENT 'Provider identifier',
        customer_id BIGINT NOT NULL,
        interaction_type ENUM('job_view', 'job_application', 'booking', 'message', 'job_completed') NOT NULL,
        job_id BIGINT NULL,
        booking_id BIGINT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        INDEX idx_provider_customer (provider_id, customer_id),
        INDEX idx_customer (customer_id),
        INDEX idx_interaction_type (interaction_type),
        INDEX idx_created_at (created_at),
        
        UNIQUE KEY unique_interaction (provider_id, customer_id, interaction_type, job_id, booking_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    COMMENT='Tracks provider-customer interactions for profile access control'
    """
    
    try:
        with conn.cursor() as cur:
            cur.execute(migration_sql)
            conn.commit()
            print("✅ provider_customer_interactions table created")
            
            # Now try to add foreign keys
            print("\n📝 Adding foreign key constraints...")
            
            # Add customer foreign key
            try:
                cur.execute("""
                    ALTER TABLE provider_customer_interactions
                    ADD CONSTRAINT fk_interaction_customer 
                        FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
                """)
                conn.commit()
                print("✅ Added customer foreign key")
            except Exception as e:
                print(f"⚠️  Could not add customer foreign key (may already exist): {e}")
            
            # Add provider foreign key (may fail if types don't match exactly)
            try:
                cur.execute("""
                    ALTER TABLE provider_customer_interactions
                    ADD CONSTRAINT fk_interaction_provider 
                        FOREIGN KEY (provider_id) REFERENCES service_providers(provider_id) ON DELETE CASCADE
                """)
                conn.commit()
                print("✅ Added provider foreign key")
            except Exception as e:
                print(f"⚠️  Could not add provider foreign key: {e}")
                print("    Table will work without this constraint, but referential integrity won't be enforced")
            
            # Verify
            cur.execute("DESCRIBE provider_customer_interactions")
            columns = cur.fetchall()
            
            print("\n📋 Table Structure:")
            print("-" * 80)
            for col in columns:
                print(f"  {col['Field']:30} {col['Type']:40} {col['Null']:5} {col['Key']:5}")
            print("-" * 80)
            
            # Show indexes
            cur.execute("SHOW INDEX FROM provider_customer_interactions")
            indexes = cur.fetchall()
            
            print("\n📋 Indexes:")
            print("-" * 80)
            seen_indexes = set()
            for idx in indexes:
                index_name = idx['Key_name']
                if index_name not in seen_indexes:
                    seen_indexes.add(index_name)
                    non_unique = "No" if idx['Non_unique'] == 0 else "Yes"
                    print(f"  {index_name:40} Non-Unique: {non_unique}")
            print("-" * 80)
            
    except Exception as e:
        print(f"❌ Failed to create provider_customer_interactions table: {e}")
        raise
    
    try:
        with conn.cursor() as cur:
            cur.execute(migration_sql)
            conn.commit()
            print("✅ provider_customer_interactions table created")
            
            # Verify
            cur.execute("DESCRIBE provider_customer_interactions")
            columns = cur.fetchall()
            
            print("\n📋 Table Structure:")
            print("-" * 80)
            for col in columns:
                print(f"  {col['Field']:30} {col['Type']:40} {col['Null']:5} {col['Key']:5}")
            print("-" * 80)
            
            # Show indexes
            cur.execute("SHOW INDEX FROM provider_customer_interactions")
            indexes = cur.fetchall()
            
            print("\n📋 Indexes:")
            print("-" * 80)
            seen_indexes = set()
            for idx in indexes:
                index_name = idx['Key_name']
                if index_name not in seen_indexes:
                    seen_indexes.add(index_name)
                    non_unique = "No" if idx['Non_unique'] == 0 else "Yes"
                    print(f"  {index_name:40} Non-Unique: {non_unique}")
            print("-" * 80)
            
    except Exception as e:
        print(f"❌ Failed to create provider_customer_interactions table: {e}")
        raise

def verify_all_migrations(conn):
    """Final verification of all Phase 1 migrations"""
    print("\n" + "="*80)
    print("🔍 Final Verification of All Migrations")
    print("="*80)
    
    with conn.cursor() as cur:
        # Check new tables
        cur.execute("""
            SELECT TABLE_NAME, TABLE_ROWS, CREATE_TIME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME IN ('customer_profile_stats', 'provider_customer_interactions')
            ORDER BY TABLE_NAME
        """)
        tables = cur.fetchall()
        
        print("\n📋 New Tables Created:")
        print("-" * 80)
        for table in tables:
            print(f"  ✅ {table['TABLE_NAME']:40} Rows: {table['TABLE_ROWS'] or 0}")
        print("-" * 80)
        
        # Check new columns in customers
        cur.execute("""
            SELECT COUNT(*) as count
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'customers'
              AND COLUMN_NAME IN ('display_name', 'profile_visibility')
        """)
        customer_cols = cur.fetchone()
        print(f"\n  ✅ customers table: {customer_cols['count']}/2 new columns added")
        
        # Check new column in provider_customer_reviews
        cur.execute("""
            SELECT COUNT(*) as count
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'provider_customer_reviews'
              AND COLUMN_NAME = 'is_visible'
        """)
        review_cols = cur.fetchone()
        print(f"  ✅ provider_customer_reviews table: {review_cols['count']}/1 new column added")

def run_all_migrations():
    """Run all Phase 1 migrations"""
    print("\n" + "="*80)
    print("🚀 Customer Public Profile - Phase 1 Migrations")
    print("="*80)
    print("Starting migrations at:", os.popen('date').read().strip())
    
    print("\n🔍 Connecting to database...")
    conn = get_connection()
    
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        # Run all migrations in order
        run_migration_1_1(conn)
        run_migration_1_2(conn)
        run_migration_1_3(conn)
        run_migration_1_4(conn)
        
        # Final verification
        verify_all_migrations(conn)
        
        print("\n" + "="*80)
        print("✅ Phase 1 Migrations Completed Successfully!")
        print("="*80)
        print("Completed at:", os.popen('date').read().strip())
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = run_all_migrations()
    sys.exit(0 if success else 1)
