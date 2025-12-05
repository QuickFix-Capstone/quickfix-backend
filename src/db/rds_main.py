import os
import pymysql
from dotenv import load_dotenv
from pymysql.constants import FIELD_TYPE

# Load environment variables from .env file
load_dotenv()
# decimal_to_float = {FIELD_TYPE.DECIMAL: float}


def get_connection():
    """
    Establishes and returns a connection to the MySQL database.
    """
    try:
        connection = pymysql.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DB"),
            cursorclass=pymysql.cursors.DictCursor,
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