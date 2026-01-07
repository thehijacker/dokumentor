#!/usr/bin/env python3
"""
Migration script to add bill_value column to documents table
"""
import sqlite3
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import config

def migrate():
    db_path = config.get('database.path', './data/documents.db')
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(documents)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'bill_value' in columns:
            print("Column 'bill_value' already exists. Skipping migration.")
            return
        
        print("Adding 'bill_value' column to documents table...")
        cursor.execute("""
            ALTER TABLE documents 
            ADD COLUMN bill_value REAL
        """)
        
        conn.commit()
        print("✓ Successfully added 'bill_value' column")
        
    except Exception as e:
        print(f"✗ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
    print("\nMigration completed!")
