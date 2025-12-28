import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def check_table():
    try:
        connection = pymysql.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DB"),
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            # Try to select from the table
            try:
                cursor.execute("SELECT 1 FROM service_providers LIMIT 1")
                print("Table 'service_providers' STILL EXISTS.")
            except pymysql.ProgrammingError as e:
                if e.args[0] == 1146: # Table doesn't exist
                    print("Table 'service_providers' does not exist (Verified).")
                else:
                    print(f"Error checking table: {e}")
        connection.close()
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    check_table()
