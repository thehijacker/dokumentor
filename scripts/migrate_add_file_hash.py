#!/usr/bin/env python3
"""
Migration script to add file_hash column to documents table
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db
from sqlalchemy import text


def migrate():
    """Add file_hash column to documents table"""
    db = get_db()
    
    try:
        # Check if column already exists
        result = db.execute(text("PRAGMA table_info(documents)")).fetchall()
        columns = [row[1] for row in result]
        
        if 'file_hash' in columns:
            print("✅ Column 'file_hash' already exists")
            return
        
        # Add the column
        print("Adding 'file_hash' column to documents table...")
        db.execute(text("ALTER TABLE documents ADD COLUMN file_hash VARCHAR(64)"))
        db.commit()
        
        # Create index
        print("Creating index on 'file_hash' column...")
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash)"))
        db.commit()
        
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    print("=" * 60)
    print("DATABASE MIGRATION: Add file_hash column")
    print("=" * 60)
    migrate()
