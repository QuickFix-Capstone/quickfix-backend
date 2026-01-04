# src/db/provider_certifications.py

import os
import pymysql
from dotenv import load_dotenv
from typing import Optional, Dict, Any

load_dotenv()


MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))


def get_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        port=MYSQL_PORT,
        cursorclass=pymysql.cursors.DictCursor,
    )


def add_provider_certification(
    provider_id: int,
    cert_url: str,
    cert_type: Optional[str] = None
) -> Dict[str, Any]:
    if not provider_id or not cert_url:
        return {"success": False, "error": "provider_id and cert_url are required"}

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            sql = """
                INSERT INTO provider_certifications (provider_id, cert_url, cert_type)
                VALUES (%s, %s, %s)
            """
            cur.execute(sql, (provider_id, cert_url, cert_type))
            conn.commit()
            return {"success": True, "cert_id": cur.lastrowid}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Test the function
    print("---- Testing add_provider_certification ----")
    
    # 1. Create a dummy provider first (needed for foreign key)
    conn = get_connection()
    provider_id = None
    try:
        with conn.cursor() as cur:
            # Insert dummy provider
            cur.execute("""
                INSERT INTO service_providers (email, first_name, last_name, category, business_name)
                VALUES ('test_cert_provider@example.com', 'Test', 'Provider', 'plumber', 'Test Biz')
            """)
            provider_id = cur.lastrowid
            conn.commit()
            print(f"✅ Created dummy provider with ID: {provider_id}")

            # 2. Test adding certification
            cert_url = "https://example.com/cert.pdf"
            cert_type = "License"
            
            print(f"Adding certification for provider {provider_id}...")
            result = add_provider_certification(provider_id, cert_url, cert_type)
            
            if result["success"]:
                print(f"✅ Certification added! ID: {result['cert_id']}")
            else:
                print(f"❌ Failed to add certification: {result.get('error')}")

    except Exception as e:
        print(f"❌ Test Setup Failed: {e}")
    finally:
        # 3. Cleanup
        if provider_id:
            try:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM service_providers WHERE provider_id = %s", (provider_id,))
                    conn.commit()
                    print("✅ Cleanup successful (deleted dummy provider)")
            except Exception as e:
                print(f"❌ Cleanup Failed: {e}")
        conn.close()

