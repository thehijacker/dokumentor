#!/usr/bin/env python3
"""
Script to remove duplicate documents from the database.
Keeps the oldest document with its learning records.
Deletes newer duplicates without breaking the AI model.
"""

import sys
import os
import hashlib

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db, Document, LearningRecord
from sqlalchemy.orm import joinedload
from collections import defaultdict


def calculate_file_hash(file_path):
    """Calculate SHA256 hash of a file"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        print(f"Error calculating hash for {file_path}: {e}")
        return None


def find_duplicates():
    """Find all duplicate documents"""
    db = get_db()
    
    # Get all documents with eager loading of learning_records
    documents = db.query(Document).options(joinedload(Document.learning_records)).all()
    print(f"Found {len(documents)} total documents")
    
    # Calculate hashes for documents that don't have one
    print("\nCalculating missing file hashes...")
    updated = 0
    for doc in documents:
        if not doc.file_hash and os.path.exists(doc.file_path):
            file_hash = calculate_file_hash(doc.file_path)
            if file_hash:
                doc.file_hash = file_hash
                updated += 1
                if updated % 10 == 0:
                    print(f"  Updated {updated} hashes...")
    
    if updated > 0:
        db.commit()
        print(f"Updated {updated} documents with file hashes")
    
    # Group by user_id and file_hash
    hash_groups = defaultdict(list)
    for doc in documents:
        if doc.file_hash:
            key = (doc.user_id, doc.file_hash)
            hash_groups[key].append(doc)
    
    # Find duplicates (groups with more than 1 document)
    duplicates = {key: docs for key, docs in hash_groups.items() if len(docs) > 1}
    
    db.close()
    return duplicates


def cleanup_duplicates(dry_run=True):
    """Remove duplicate documents, keeping the oldest one"""
    duplicates = find_duplicates()
    
    if not duplicates:
        print("\n✅ No duplicates found!")
        return
    
    total_docs = sum(len(docs) for docs in duplicates.values())
    total_to_delete = sum(len(docs) - 1 for docs in duplicates.values())
    
    print(f"\n📊 Found {len(duplicates)} groups of duplicates")
    print(f"   Total duplicate documents: {total_docs}")
    print(f"   Documents to delete: {total_to_delete}")
    print(f"   Documents to keep: {len(duplicates)}")
    
    if dry_run:
        print("\n🔍 DRY RUN - Showing what would be deleted:\n")
    else:
        print("\n🗑️  DELETING DUPLICATES:\n")
    
    db = get_db()
    deleted_count = 0
    kept_count = 0
    
    for (user_id, file_hash), docs in duplicates.items():
        # Sort by creation date (keep oldest)
        docs.sort(key=lambda d: d.created_at)
        
        keep_doc = docs[0]
        delete_docs = docs[1:]
        
        print(f"📄 File: {keep_doc.original_filename}")
        print(f"   Keeping:  ID={keep_doc.id}, Created={keep_doc.created_at.strftime('%Y-%m-%d %H:%M')}")
        kept_count += 1
        
        for doc in delete_docs:
            learning_count = db.query(LearningRecord).filter_by(document_id=doc.id).count()
            print(f"   Deleting: ID={doc.id}, Created={doc.created_at.strftime('%Y-%m-%d %H:%M')}, LearningRecords={learning_count}")
            
            if not dry_run:
                # Delete physical file
                if os.path.exists(doc.file_path):
                    try:
                        os.remove(doc.file_path)
                    except Exception as e:
                        print(f"      ⚠️  Could not delete file: {e}")
                
                # Delete from database (learning records cascade)
                db.delete(doc)
                deleted_count += 1
        
        print()
    
    if not dry_run:
        db.commit()
        print(f"✅ Deleted {deleted_count} duplicate documents")
        print(f"✅ Kept {kept_count} original documents")
        print(f"✅ Learning records preserved in kept documents")
    else:
        print("ℹ️  This was a dry run. Run with --execute to actually delete duplicates.")
    
    db.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Remove duplicate documents')
    parser.add_argument('--execute', action='store_true', 
                       help='Actually delete duplicates (default is dry run)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("DUPLICATE DOCUMENT CLEANUP SCRIPT")
    print("=" * 60)
    
    cleanup_duplicates(dry_run=not args.execute)
