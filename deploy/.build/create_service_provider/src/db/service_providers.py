try:
    from .rds_main import get_connection
except ImportError:
    from rds_main import get_connection

def create_service_provider_in_db(data):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            sql = """
                INSERT INTO service_providers
                (email, first_name, last_name, phone,
                 business_name, bio, category,
                 city, state, postal_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql, (
                data["email"],
                data["first_name"],
                data["last_name"],
                data.get("phone"),
                data.get("business_name"),
                data.get("bio"),
                data["category"],
                data.get("city"),
                data.get("state"),
                data.get("postal_code"),
            ))

            conn.commit()
            return {
                "success": True,
                "provider_id": cur.lastrowid
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    print("---- Testing create_service_provider_in_db ----")
    
    test_data = {
        "email": "test_provider_db@example.com",
        "first_name": "Test",
        "last_name": "ProviderDB",
        "phone": "1234567890",
        "business_name": "Test DB Biz",
        "bio": "I am a test provider",
        "category": "electrician",
        "city": "Test City",
        "state": "TS",
        "postal_code": "12345"
    }

    provider_id = None
    conn = get_connection()
    
    try:
        print(f"Creating service provider: {test_data['email']}...")
        result = create_service_provider_in_db(test_data)
        
        if result["success"]:
            provider_id = result["provider_id"]
            print(f"✅ Service Provider created! ID: {provider_id}")
        else:
            print(f"❌ Failed to create service provider: {result.get('error')}")

    except Exception as e:
        print(f"❌ Test Execution Failed: {e}")
    
    finally:
        # Cleanup
        if provider_id:
            try:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM service_providers WHERE provider_id = %s", (provider_id,))
                    conn.commit()
                    print("✅ Cleanup successful (deleted dummy provider)")
            except Exception as e:
                print(f"❌ Cleanup Failed: {e}")
        conn.close()