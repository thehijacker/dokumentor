#!/usr/bin/env python3
"""
Script to populate bill_value for existing documents from extracted_data
"""
import sqlite3
import sys
import os
import json
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import config

def extract_bill_value(extracted_data_json):
    """Extract bill value from extracted_data JSON"""
    if not extracted_data_json:
        return None
    
    try:
        data = json.loads(extracted_data_json)
        if 'amounts' in data and data['amounts']:
            # Get first amount and convert to float
            amount_str = data['amounts'][0].replace(',', '.')
            return float(amount_str)
    except (json.JSONDecodeError, ValueError, IndexError):
        pass
    
    return None

def populate_bill_values():
    db_path = config.get('database.path', './data/documents.db')
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all documents with extracted_data but no bill_value
        cursor.execute("""
            SELECT id, extracted_data 
            FROM documents 
            WHERE extracted_data IS NOT NULL 
            AND (bill_value IS NULL OR bill_value = 0)
        """)
        
        documents = cursor.fetchall()
        print(f"Found {len(documents)} documents to process")
        
        updated_count = 0
        for doc_id, extracted_data in documents:
            bill_value = extract_bill_value(extracted_data)
            if bill_value is not None:
                cursor.execute("""
                    UPDATE documents 
                    SET bill_value = ? 
                    WHERE id = ?
                """, (bill_value, doc_id))
                updated_count += 1
                print(f"  Document {doc_id}: {bill_value:.2f} €")
        
        conn.commit()
        print(f"\n✓ Successfully updated {updated_count} documents with bill values")
        print(f"✓ {len(documents) - updated_count} documents had no extractable amounts")
        
    except Exception as e:
        print(f"✗ Error during processing: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    populate_bill_values()
    print("\nProcessing completed!")
