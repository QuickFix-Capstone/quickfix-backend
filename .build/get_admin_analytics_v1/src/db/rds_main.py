import os
import pymysql
import json

# Load environment variables from .env file (only for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available (e.g., in Lambda), use environment variables directly
    pass


def get_connection():
    """
    Establishes and returns a connection to the MySQL database.
    """
    try:
        host = os.getenv("MYSQL_HOST") or os.getenv("DB_HOST")
        user = os.getenv("MYSQL_USER") or os.getenv("DB_USER")
        password = os.getenv("MYSQL_PASSWORD") or os.getenv("DB_PASSWORD")
        database = os.getenv("MYSQL_DB") or os.getenv("DB_NAME")
        port = int(os.getenv("MYSQL_PORT") or os.getenv("DB_PORT") or 3306)

        # Backward compatibility: some Lambdas store password in Secrets Manager.
        if not password:
            secret_name = os.getenv("DB_PASSWORD_SECRET_NAME")
            if secret_name:
                try:
                    import boto3
                    client = boto3.client("secretsmanager")
                    secret_value = client.get_secret_value(SecretId=secret_name)
                    secret_string = secret_value.get("SecretString", "")
                    if secret_string:
                        try:
                            secret_json = json.loads(secret_string)
                            password = (
                                secret_json.get("password")
                                or secret_json.get("MYSQL_PASSWORD")
                                or secret_json.get("db_password")
                                or secret_string
                            )
                        except json.JSONDecodeError:
                            password = secret_string
                except Exception as secret_error:
                    print(f"Error loading DB password secret: {secret_error}")

        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
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
