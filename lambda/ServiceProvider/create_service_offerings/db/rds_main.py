import os
import pymysql
from dotenv import load_dotenv
from pymysql.constants import FIELD_TYPE

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

# Load environment variables from .env file
load_dotenv()
# decimal_to_float = {FIELD_TYPE.DECIMAL: float}

def get_connection():
    """
    Establishes and returns a connection to the MySQL database.
    """
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
            # conv=decimal_to_float
        )
        return connection
    except pymysql.MySQLError as e:
        print(f"Error connecting to MySQL Platform: {e}")
        return None

if __name__ == "__main__":
    conn = get_connection()
    if conn:
        print("Connection successful!")
        conn.close()
    else:
        print("Connection failed.")