"""
Migration script to add user-specific fields
- pdf_passwords field to users table
- user_id field to learning_records table
Run this once to update the database schema
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
import backend.database as db_module

def migrate():
    """Add user-specific columns"""
    print("Starting migration: Add user-specific fields")
    
    # Initialize database first
    db_module.init_db()
    
    # Now access the engine after initialization
    engine = db_module.engine
    
    if engine is None:
        print("✗ Failed to initialize database engine")
        return False
    
    try:
        with engine.connect() as conn:
            # 1. Add pdf_passwords to users table
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]
            
            if 'pdf_passwords' not in columns:
                print("Adding pdf_passwords column to users...")
                conn.execute(text("ALTER TABLE users ADD COLUMN pdf_passwords TEXT"))
                conn.commit()
                print("✓ pdf_passwords column added successfully")
            else:
                print("✓ pdf_passwords column already exists")
            
            # 2. Add user_id to learning_records table
            result = conn.execute(text("PRAGMA table_info(learning_records)"))
            columns = [row[1] for row in result]
            
            if 'user_id' not in columns:
                print("Adding user_id column to learning_records...")
                conn.execute(text("ALTER TABLE learning_records ADD COLUMN user_id INTEGER"))
                conn.commit()
                print("✓ user_id column added to learning_records")
                
                # Update existing records to use user_id from their documents
                print("Updating existing learning_records with user_id from documents...")
                conn.execute(text("""
                    UPDATE learning_records 
                    SET user_id = (
                        SELECT user_id 
                        FROM documents 
                        WHERE documents.id = learning_records.document_id
                    )
                    WHERE user_id IS NULL
                """))
                conn.commit()
                print("✓ Existing records updated")
            else:
                print("✓ user_id column already exists in learning_records")
        
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
