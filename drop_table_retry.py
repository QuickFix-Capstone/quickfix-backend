import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def drop_table():
    print(f"Connecting to database...")
    try:
        connection = pymysql.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DB"),
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        print("Connected.")
        with connection.cursor() as cursor:
            print("Executing DROP TABLE service_providers...")
            sql = "DROP TABLE service_providers;" # Removing IF EXISTS to force error if not there
            cursor.execute(sql)
            print("DROP executed.")
        
        connection.close()
        print("Connection closed.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    drop_table()
