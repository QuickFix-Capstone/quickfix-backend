"""
Migration script to run SQL migrations for the review system
"""
import os
import pymysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
connection = pymysql.connect(
    host=os.getenv('MYSQL_HOST'),
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASSWORD'),
    database=os.getenv('MYSQL_DB'),
    port=int(os.getenv('MYSQL_PORT', 3306))
)

try:
    cursor = connection.cursor()

    print("=" * 60)
    print("Starting Migration: Review System")
    print("=" * 60)

    # Check existing columns in service_providers
    print("\n1. Checking service_providers table...")
    cursor.execute("DESCRIBE service_providers")
    sp_columns = [row[0] for row in cursor.fetchall()]

    # Check existing columns in customers
    print("2. Checking customers table...")
    cursor.execute("DESCRIBE customers")
    cust_columns = [row[0] for row in cursor.fetchall()]

    # Check if reviews table exists
    print("3. Checking reviews table...")
    cursor.execute("SHOW TABLES LIKE 'reviews'")
    reviews_exists = cursor.fetchone() is not None

    # Add missing columns to customers
    print("\n" + "=" * 60)
    print("Running Migrations...")
    print("=" * 60)

    if 'total_rating_points' not in cust_columns:
        print("\n✓ Adding total_rating_points to customers...")
        cursor.execute("""
            ALTER TABLE customers
            ADD COLUMN total_rating_points INT NOT NULL DEFAULT 0
            COMMENT 'Sum of all ratings received from providers'
        """)
    else:
        print("\n- Skipped: total_rating_points already exists in customers")

    if 'total_review_count' not in cust_columns:
        print("✓ Adding total_review_count to customers...")
        cursor.execute("""
            ALTER TABLE customers
            ADD COLUMN total_review_count INT NOT NULL DEFAULT 0
            COMMENT 'Total number of reviews received from providers'
        """)
    else:
        print("- Skipped: total_review_count already exists in customers")

    if 'average_rating' not in cust_columns:
        print("✓ Adding average_rating to customers...")
        cursor.execute("""
            ALTER TABLE customers
            ADD COLUMN average_rating DECIMAL(3, 2) NOT NULL DEFAULT 0.00
            COMMENT 'Calculated average rating (total_rating_points / total_review_count)'
        """)
    else:
        print("- Skipped: average_rating already exists in customers")

    # Add index to customers
    print("✓ Adding index idx_customer_rating to customers...")
    try:
        cursor.execute("CREATE INDEX idx_customer_rating ON customers(average_rating DESC)")
        print("  Index created successfully")
    except pymysql.err.OperationalError as e:
        if "Duplicate key name" in str(e):
            print("  - Skipped: Index already exists")
        else:
            raise

    # Update service_providers rating column comment
    print("\n✓ Updating service_providers.rating column comment...")
    cursor.execute("""
        ALTER TABLE service_providers
        MODIFY COLUMN rating DECIMAL(3, 2) DEFAULT 0.00
        COMMENT 'Average rating calculated from reviews (total_rating_points / total_review_count)'
    """)

    connection.commit()

    print("\n" + "=" * 60)
    print("Migration Completed Successfully!")
    print("=" * 60)

    # Show final state
    print("\nFinal customers table structure:")
    cursor.execute("DESCRIBE customers")
    for row in cursor.fetchall():
        if 'rating' in row[0]:
            print(f"  - {row[0]}: {row[1]}")

    print("\nFinal service_providers rating fields:")
    cursor.execute("DESCRIBE service_providers")
    for row in cursor.fetchall():
        if 'rating' in row[0]:
            print(f"  - {row[0]}: {row[1]}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    connection.rollback()
    raise
finally:
    cursor.close()
    connection.close()
