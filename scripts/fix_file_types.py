#!/usr/bin/env python3
"""
Script to fix file_type values to be lowercase for consistency
"""
import sqlite3
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import config

def fix_file_types():
    db_path = config.get('database.path', './data/documents.db')
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all documents with uppercase file_type
        cursor.execute("""
            SELECT id, file_type, original_filename
            FROM documents 
            WHERE file_type != lower(file_type)
        """)
        
        documents = cursor.fetchall()
        print(f"Found {len(documents)} documents with uppercase file_type")
        
        for doc_id, file_type, filename in documents:
            new_file_type = file_type.lower()
            cursor.execute("""
                UPDATE documents 
                SET file_type = ? 
                WHERE id = ?
            """, (new_file_type, doc_id))
            print(f"  {filename}: {file_type} -> {new_file_type}")
        
        conn.commit()
        print(f"\n✓ Successfully updated {len(documents)} documents")
        
    except Exception as e:
        print(f"✗ Error during processing: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    fix_file_types()
    print("\nProcessing completed!")
