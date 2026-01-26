#!/usr/bin/env python3
"""
Run database migration for booking_images table
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.db.rds_main import get_connection

def run_migration():
    """Run the booking_images table migration."""

    migration_sql = """
CREATE TABLE IF NOT EXISTS booking_images (
    image_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    booking_id BIGINT NOT NULL,
    image_key VARCHAR(512) NOT NULL COMMENT 'S3 key (e.g., booking-images/123/photo.jpg)',
    image_order TINYINT NOT NULL DEFAULT 1 COMMENT 'Display order (1-5)',
    content_type VARCHAR(50) NOT NULL COMMENT 'MIME type (e.g., image/jpeg)',
    file_size INT NULL COMMENT 'File size in bytes',
    description VARCHAR(255) NULL COMMENT 'Optional image description',
    uploaded_by_id BIGINT NOT NULL COMMENT 'Customer ID who uploaded',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_booking_image_booking
        FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE CASCADE,
    CONSTRAINT fk_booking_image_customer
        FOREIGN KEY (uploaded_by_id) REFERENCES customers(customer_id) ON DELETE CASCADE,

    INDEX idx_booking_id (booking_id),
    INDEX idx_uploaded_by_id (uploaded_by_id),
    INDEX idx_image_order (booking_id, image_order),

    CONSTRAINT chk_image_order CHECK (image_order BETWEEN 1 AND 5),
    UNIQUE KEY unique_booking_order (booking_id, image_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

    print("🔍 Connecting to database...")
    conn = get_connection()

    if not conn:
        print("❌ Failed to connect to database")
        return False

    try:
        with conn.cursor() as cur:
            print("📝 Running migration: Create booking_images table...")
            cur.execute(migration_sql)
            conn.commit()
            print("✅ Migration successful!")

            # Verify table was created
            print("\n🔍 Verifying table structure...")
            cur.execute("DESCRIBE booking_images")
            columns = cur.fetchall()

            print("\n📋 Table Structure:")
            print("-" * 80)
            for col in columns:
                print(f"  {col['Field']:20} {col['Type']:20} {col['Null']:5} {col['Key']:5} {col['Default'] or ''}")
            print("-" * 80)

            # Check indexes
            print("\n🔍 Checking indexes...")
            cur.execute("SHOW INDEX FROM booking_images")
            indexes = cur.fetchall()

            print("\n📋 Indexes:")
            print("-" * 80)
            unique_indexes = set()
            for idx in indexes:
                index_name = idx['Key_name']
                if index_name not in unique_indexes:
                    unique_indexes.add(index_name)
                    non_unique = "No" if idx['Non_unique'] == 0 else "Yes"
                    print(f"  {index_name:30} Non-Unique: {non_unique}")
            print("-" * 80)

            return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

    finally:
        conn.close()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
