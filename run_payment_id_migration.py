#!/usr/bin/env python3
"""
Script to run the payment id column rename migration
"""

import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get database connection from environment variables"""
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DB', 'quickfix'),
        port=int(os.getenv('MYSQL_PORT', 3306))
    )

def check_foreign_keys():
    """Check for foreign key constraints referencing payment.id"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        TABLE_NAME,
        COLUMN_NAME,
        CONSTRAINT_NAME,
        REFERENCED_TABLE_NAME,
        REFERENCED_COLUMN_NAME
    FROM information_schema.KEY_COLUMN_USAGE 
    WHERE REFERENCED_TABLE_NAME = 'payment' AND REFERENCED_COLUMN_NAME = 'id'
    """
    
    cursor.execute(query)
    foreign_keys = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return foreign_keys

def run_migration():
    """Run the payment id column rename migration"""
    # First check for foreign keys
    foreign_keys = check_foreign_keys()
    
    if foreign_keys:
        print("WARNING: Found foreign key constraints referencing payment.id:")
        for fk in foreign_keys:
            print(f"  - {fk[0]}.{fk[1]} -> {fk[3]}.{fk[4]} (constraint: {fk[2]})")
        print("You may need to update these foreign keys after the migration.")
        
        response = input("Continue with migration? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return False
    
    # Run the migration
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("Running migration: Renaming payment.id to payment.payment_id...")
        
        # Read and execute the migration SQL
        with open('sql/migrations/rename_payment_id_column.sql', 'r') as f:
            migration_sql = f.read()
        
        # Execute the main ALTER TABLE command
        alter_command = "ALTER TABLE `payment` CHANGE COLUMN `id` `payment_id` int NOT NULL AUTO_INCREMENT;"
        cursor.execute(alter_command)
        
        # Commit the changes
        conn.commit()
        
        print("Migration completed successfully!")
        
        # Verify the change
        cursor.execute("DESCRIBE payment")
        columns = cursor.fetchall()
        print("\nUpdated payment table structure:")
        for col in columns:
            print(f"  {col[0]} - {col[1]} - {col[2]} - {col[3]} - {col[4]} - {col[5]}")
            
        return True
        
    except mysql.connector.Error as err:
        print(f"Error running migration: {err}")
        conn.rollback()
        return False
        
    finally:
        cursor.close()
        conn.close()

def rollback_migration():
    """Rollback the payment id column rename migration"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("Running rollback: Renaming payment.payment_id back to payment.id...")
        
        # Execute the rollback command
        rollback_command = "ALTER TABLE `payment` CHANGE COLUMN `payment_id` `id` int NOT NULL AUTO_INCREMENT;"
        cursor.execute(rollback_command)
        
        # Commit the changes
        conn.commit()
        
        print("Rollback completed successfully!")
        
        # Verify the change
        cursor.execute("DESCRIBE payment")
        columns = cursor.fetchall()
        print("\nRolled back payment table structure:")
        for col in columns:
            print(f"  {col[0]} - {col[1]} - {col[2]} - {col[3]} - {col[4]} - {col[5]}")
            
        return True
        
    except mysql.connector.Error as err:
        print(f"Error running rollback: {err}")
        conn.rollback()
        return False
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        run_migration()