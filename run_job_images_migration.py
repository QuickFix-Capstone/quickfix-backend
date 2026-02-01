#!/usr/bin/env python3
"""
Run database migration for job_images table
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.db.rds_main import get_connection


def run_migration():
    """Run the job_images table migration."""
    
    migration_sql = """
CREATE TABLE IF NOT EXISTS job_images (
    image_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT NOT NULL,
    image_key VARCHAR(512) NOT NULL COMMENT 'S3 key (e.g., job-images/123/photo.jpg)',
    image_order TINYINT NOT NULL DEFAULT 1 COMMENT 'Display order (1-5)',
    content_type VARCHAR(50) NOT NULL COMMENT 'MIME type (e.g., image/jpeg)',
    file_size INT NULL COMMENT 'File size in bytes',
    description VARCHAR(255) NULL COMMENT 'Optional image description',
    uploaded_by_id BIGINT NOT NULL COMMENT 'Customer ID who uploaded',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_job_image_job
        FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
    CONSTRAINT fk_job_image_customer
        FOREIGN KEY (uploaded_by_id) REFERENCES customers(customer_id) ON DELETE CASCADE,

    INDEX idx_job_id (job_id),
    INDEX idx_uploaded_by_id (uploaded_by_id),
    INDEX idx_image_order (job_id, image_order),

    CONSTRAINT chk_job_image_order CHECK (image_order BETWEEN 1 AND 5),
    UNIQUE KEY unique_job_order (job_id, image_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""
    
    conn = get_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        with conn.cursor() as cur:
            print("📝 Running migration: Create job_images table...")
            cur.execute(migration_sql)
            conn.commit()
            print("✅ Migration completed successfully!")
            
            # Verify table was created
            print("\n📋 Verifying table structure...")
            cur.execute("DESCRIBE job_images")
            columns = cur.fetchall()
            
            print("\nTable: job_images")
            print("-" * 80)
            for col in columns:
                print(f"  {col['Field']:20} {col['Type']:20} {col['Null']:5} {col['Key']:5}")
            
            # Show indexes
            print("\n📑 Indexes:")
            cur.execute("SHOW INDEX FROM job_images")
            indexes = cur.fetchall()
            for idx in indexes:
                print(f"  {idx['Key_name']:30} on {idx['Column_name']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
