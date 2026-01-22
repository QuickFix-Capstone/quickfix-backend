import os
import pymysql
from pymysql.constants import FIELD_TYPE

# Load .env ONLY for local development
if os.getenv("AWS_EXECUTION_ENV") is None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not installed in Lambda

DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_NAME = os.environ.get("DB_NAME")


def get_connection():
    """
    Creates and returns a MySQL database connection.
    Raises an exception if connection fails.
    """
    if not all([DB_HOST, DB_USER, DB_PASS, DB_NAME]):
        raise RuntimeError("Database environment variables are not fully set")

    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
