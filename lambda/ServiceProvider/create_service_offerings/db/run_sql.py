import os
import pymysql
from dotenv import load_dotenv
from rds_main import get_connection

# Load environment variables
load_dotenv()

def run_sql_file(filename):
    """
    Reads a SQL file and executes its commands.
    """
    conn = get_connection()
    if not conn:
        print("Failed to connect to database.")
        return

    try:
        with conn.cursor() as cursor:
            with open(filename, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Split by semicolon to get individual statements
            # This is a basic split and might need refinement for complex SQL (e.g. stored procs)
            statements = sql_content.split(';')
            
            for statement in statements:
                if statement.strip():
                    try:
                        cursor.execute(statement)
                        print(f"Executed: {statement[:50]}...")
                    except pymysql.MySQLError as e:
                        print(f"Error executing statement: {statement[:50]}...\nError: {e}")
            
            conn.commit()
            print("Finished executing SQL file.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Adjust path as needed relative to where script is run
    # Assuming script is run from project root: python src/db/run_sql.py
    sql_file_path = os.path.join("sql", "quickfix-mysql.sql")
    
    if os.path.exists(sql_file_path):
        print(f"Running SQL file: {sql_file_path}")
        run_sql_file(sql_file_path)
    else:
        print(f"SQL file not found at: {sql_file_path}")
