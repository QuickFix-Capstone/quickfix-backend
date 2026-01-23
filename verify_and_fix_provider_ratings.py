"""
Verify and fix service_providers rating fields
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
    print("Verifying service_providers rating fields")
    print("=" * 60)

    # Check existing columns in service_providers
    cursor.execute("DESCRIBE service_providers")
    sp_columns = {row[0]: row[1] for row in cursor.fetchall()}

    print("\nCurrent rating-related columns in service_providers:")
    for col, col_type in sp_columns.items():
        if 'rating' in col.lower():
            print(f"  ✓ {col}: {col_type}")

    # Required fields
    required_fields = {
        'rating': 'decimal(3,2)',
        'total_rating_points': 'int',
        'total_review_count': 'int'
    }

    print("\n" + "=" * 60)
    print("Checking required fields...")
    print("=" * 60)

    missing_fields = []
    for field, field_type in required_fields.items():
        if field not in sp_columns:
            missing_fields.append(field)
            print(f"  ✗ Missing: {field}")
        else:
            print(f"  ✓ Found: {field}")

    if missing_fields:
        print("\n" + "=" * 60)
        print("Adding missing fields...")
        print("=" * 60)

        for field in missing_fields:
            if field == 'total_rating_points':
                print(f"\n✓ Adding {field}...")
                cursor.execute("""
                    ALTER TABLE service_providers
                    ADD COLUMN total_rating_points INT NOT NULL DEFAULT 0
                    COMMENT 'Sum of all ratings received'
                """)
            elif field == 'total_review_count':
                print(f"✓ Adding {field}...")
                cursor.execute("""
                    ALTER TABLE service_providers
                    ADD COLUMN total_review_count INT NOT NULL DEFAULT 0
                    COMMENT 'Total number of reviews received'
                """)
            elif field == 'rating':
                print(f"✓ Adding {field}...")
                cursor.execute("""
                    ALTER TABLE service_providers
                    ADD COLUMN rating DECIMAL(3, 2) DEFAULT 0.00
                    COMMENT 'Average rating calculated from reviews'
                """)

        connection.commit()
        print("\n✓ All missing fields added successfully!")
    else:
        print("\n✓ All required fields already exist!")

    # Verify final state
    print("\n" + "=" * 60)
    print("Final service_providers rating fields:")
    print("=" * 60)
    cursor.execute("DESCRIBE service_providers")
    for row in cursor.fetchall():
        if 'rating' in row[0].lower():
            print(f"  • {row[0]}: {row[1]}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    connection.rollback()
    raise
finally:
    cursor.close()
    connection.close()
