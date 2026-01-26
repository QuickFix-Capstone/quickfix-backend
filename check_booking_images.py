#!/usr/bin/env python3
"""
Check booking_images table records
"""
import sys
sys.path.insert(0, '.')

from src.db.rds_main import get_connection

conn = get_connection()

try:
    with conn.cursor() as cur:
        # Check total count
        cur.execute("SELECT COUNT(*) as count FROM booking_images")
        count = cur.fetchone()['count']
        print(f"📊 Total records in booking_images: {count}")

        # Check records for booking 75
        cur.execute("""
            SELECT image_id, booking_id, image_key, image_order, content_type,
                   file_size, description, created_at
            FROM booking_images
            WHERE booking_id = 75
            ORDER BY image_order
        """)
        images = cur.fetchall()

        print(f"\n📷 Images for booking 75: {len(images)} records")

        if images:
            print("\n" + "="*80)
            for img in images:
                print(f"Image ID: {img['image_id']}")
                print(f"  Order: {img['image_order']}")
                print(f"  S3 Key: {img['image_key']}")
                print(f"  Type: {img['content_type']}")
                print(f"  Size: {img['file_size']} bytes" if img['file_size'] else "  Size: N/A")
                print(f"  Description: {img['description']}")
                print(f"  Created: {img['created_at']}")
                print("-"*80)
        else:
            print("\n⚠️  No images found for booking 75")
            print("\n💡 Why? The upload-url endpoint only generates presigned URLs.")
            print("   It does NOT save records to the database.")
            print("\n   To save records, you need to:")
            print("   1. ✅ Get presigned URL (upload-url endpoint) - DONE")
            print("   2. ⏳ Upload actual image to S3 using that URL")
            print("   3. ⏳ Call create_booking_image endpoint to save metadata")

finally:
    conn.close()
