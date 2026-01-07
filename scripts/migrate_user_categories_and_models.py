"""
Migration script to make categories user-specific and migrate old model files
- Add user_id to categories table
- Add user_id to subcategories table
- Assign existing categories to user 1
- Rename old model files to user_1_* format
"""
import sys
import os
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
import backend.database as db_module

def migrate():
    """Make categories user-specific and migrate models"""
    print("Starting migration: User-specific categories and model files")
    
    # Initialize database first
    db_module.init_db()
    
    # Now access the engine after initialization
    engine = db_module.engine
    
    if engine is None:
        print("✗ Failed to initialize database engine")
        return False
    
    try:
        with engine.connect() as conn:
            # 1. Check if UNIQUE constraint exists on categories.name and remove it
            result = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='categories'"))
            create_sql = result.fetchone()
            
            needs_recreation = False
            if create_sql and 'UNIQUE' in create_sql[0]:
                print("UNIQUE constraint found on categories table, recreating...")
                needs_recreation = True
            
            result = conn.execute(text("PRAGMA table_info(categories)"))
            columns = {row[1]: row for row in result}
            
            if 'user_id' not in columns:
                print("user_id column missing, recreating table...")
                needs_recreation = True
            
            if needs_recreation:
                print("Recreating categories table to remove UNIQUE constraint...")
                
                # Create new table without UNIQUE constraint on name
                conn.execute(text("""
                    CREATE TABLE categories_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )
                """))
                
                # Copy data from old table
                if 'user_id' in columns:
                    conn.execute(text("""
                        INSERT INTO categories_new (id, user_id, name, description, created_at)
                        SELECT id, user_id, name, description, created_at FROM categories
                    """))
                else:
                    # Assign to user 1 if no user_id exists
                    conn.execute(text("""
                        INSERT INTO categories_new (id, user_id, name, description, created_at)
                        SELECT id, 1, name, description, created_at FROM categories
                    """))
                
                # Drop old table and rename new one
                conn.execute(text("DROP TABLE categories"))
                conn.execute(text("ALTER TABLE categories_new RENAME TO categories"))
                
                conn.commit()
                print("✓ Categories table recreated (no UNIQUE constraint on name)")
            else:
                print("✓ Categories table already correct")
            
            # 2. Recreate subcategories table to add user_id
            result = conn.execute(text("PRAGMA table_info(subcategories)"))
            columns = {row[1]: row for row in result}
            
            if 'user_id' not in columns:
                print("Recreating subcategories table to add user_id...")
                
                # Create new table with user_id
                conn.execute(text("""
                    CREATE TABLE subcategories_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        category_id INTEGER NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users(id),
                        FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
                    )
                """))
                
                # Copy data from old table, assigning to user 1
                conn.execute(text("""
                    INSERT INTO subcategories_new (id, user_id, name, category_id, created_at)
                    SELECT id, 1, name, category_id, created_at FROM subcategories
                """))
                
                # Drop old table and rename new one
                conn.execute(text("DROP TABLE subcategories"))
                conn.execute(text("ALTER TABLE subcategories_new RENAME TO subcategories"))
                
                conn.commit()
                print("✓ Subcategories table recreated with user_id")
            else:
                print("✓ user_id column already exists in subcategories")
        
        # 3. Migrate model files
        print("\nMigrating model files...")
        models_dir = './data/models'
        if os.path.exists(models_dir):
            old_files = [
                'category_model.pkl',
                'subcategory_1_model.pkl',
                'subcategory_4_model.pkl',
                'subcategory_5_model.pkl'
            ]
            
            for old_file in old_files:
                old_path = os.path.join(models_dir, old_file)
                if os.path.exists(old_path):
                    # Determine new filename
                    if old_file.startswith('category_'):
                        new_file = 'user_1_category_model.pkl'
                    elif old_file.startswith('subcategory_'):
                        # Extract category ID from filename
                        cat_id = old_file.split('_')[1]
                        new_file = f'user_1_subcategory_{cat_id}_model.pkl'
                    else:
                        continue
                    
                    new_path = os.path.join(models_dir, new_file)
                    
                    # Only migrate if new file doesn't exist
                    if not os.path.exists(new_path):
                        shutil.copy2(old_path, new_path)
                        print(f"✓ Migrated {old_file} -> {new_file}")
                        os.remove(old_path)
                        print(f"✓ Removed old file {old_file}")
                    else:
                        print(f"⚠ {new_file} already exists, removing old {old_file}")
                        os.remove(old_path)
        
        print("\n✓ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
