import os
import shutil
import uuid
from datetime import datetime
from typing import Dict, Optional
from backend.config import config
from backend.database import get_db, Document
from backend.ocr_processor import OCRProcessor
from backend.ai_processor import AIProcessor
import json


class DocumentProcessor:
    """Main document processing orchestrator"""
    
    def __init__(self):
        self.documents_path = config.get('storage.documents_path', './documents')
        # Don't initialize shared processors - will create per-user in process_file
        
        # Create documents directory
        os.makedirs(self.documents_path, exist_ok=True)
    
    def _get_ai_processor(self, user_id: int) -> AIProcessor:
        """Get or create AIProcessor for specific user"""
        return AIProcessor(user_id=user_id)
    
    def process_file(self, file_path: str, user_id: int, 
                    original_filename: Optional[str] = None,
                    file_hash: Optional[str] = None,
                    ai_model: Optional[str] = None,
                    pdf_passwords: Optional[list] = None) -> Dict:
        """
        Process a document file (OCR + AI categorization)
        Returns: {
            'success': bool,
            'document_id': int,
            'error': str (if failed)
        }
        """
        if original_filename is None:
            original_filename = os.path.basename(file_path)
        
        try:
            # Step 1: OCR Processing (with user-specific passwords)
            ocr_processor = OCRProcessor(user_passwords=pdf_passwords or [])
            ocr_text, ocr_confidence, ocr_language = ocr_processor.process_file(
                file_path, original_filename
            )
            
            # Step 2: AI Categorization (with user-specific model)
            ai_processor = self._get_ai_processor(user_id)
            ai_result = ai_processor.categorize_document(ocr_text, original_filename, ai_model)
            
            # Step 3: Store document
            document_id = self._save_document(
                file_path=file_path,
                original_filename=original_filename,
                user_id=user_id,
                ocr_text=ocr_text,
                ocr_confidence=ocr_confidence,
                ocr_language=ocr_language,
                category_id=ai_result.get('category_id'),
                subcategory_id=ai_result.get('subcategory_id'),
                ai_confidence=ai_result.get('confidence'),
                extracted_data=ai_result.get('extracted_data', {}),
                file_hash=file_hash
            )
            
            return {
                'success': True,
                'document_id': document_id,
                'ocr_text': ocr_text[:500],  # First 500 chars
                'category_id': ai_result.get('category_id'),
                'subcategory_id': ai_result.get('subcategory_id'),
                'confidence': ai_result.get('confidence')
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _save_document(self, file_path: str, original_filename: str, user_id: int,
                      ocr_text: str, ocr_confidence: float, ocr_language: str,
                      category_id: Optional[int], subcategory_id: Optional[int],
                      ai_confidence: Optional[float], extracted_data: Dict,
                      file_hash: Optional[str] = None) -> int:
        """Save document to storage and database"""
        
        # Generate unique filename
        ext = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        
        # Copy file to documents directory
        dest_path = os.path.join(self.documents_path, unique_filename)
        shutil.copy2(file_path, dest_path)
        
        # Get file info
        file_size = os.path.getsize(dest_path)
        file_type = ext[1:].lower() if ext else 'unknown'
        
        # Extract bill value from extracted_data
        bill_value = None
        if extracted_data and 'amounts' in extracted_data and extracted_data['amounts']:
            try:
                # Try to parse the first amount found
                amount_str = extracted_data['amounts'][0].replace(',', '.')
                bill_value = float(amount_str)
            except (ValueError, IndexError):
                pass
        
        # Save to database
        db = get_db()
        try:
            document = Document(
                user_id=user_id,
                filename=unique_filename,
                original_filename=original_filename,
                file_path=dest_path,
                file_type=file_type,
                file_size=file_size,
                file_hash=file_hash,
                ocr_text=ocr_text,
                ocr_language=ocr_language,
                ocr_confidence=ocr_confidence,
                category_id=category_id,
                subcategory_id=subcategory_id,
                ai_confidence=ai_confidence,
                extracted_data=json.dumps(extracted_data) if extracted_data else None,
                bill_value=bill_value,
                is_processed=True,
                processed_at=datetime.utcnow()
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            document_id = document.id
            
            return document_id
        
        finally:
            db.close()
    
    def reprocess_document(self, document_id: int, ai_model: Optional[str] = None) -> Dict:
        """Reprocess an existing document"""
        db = get_db()
        try:
            document = db.query(Document).filter_by(id=document_id).first()
            
            if not document:
                return {'success': False, 'error': 'Document not found'}
            
            # Get user's PDF passwords
            from backend.database import User
            user = db.query(User).filter_by(id=document.user_id).first()
            pdf_passwords = []
            if user and user.pdf_passwords:
                try:
                    pdf_passwords = json.loads(user.pdf_passwords)
                except:
                    pass
            
            # Re-run OCR with user-specific passwords
            from backend.ocr_processor import OCRProcessor
            ocr_processor = OCRProcessor(user_passwords=pdf_passwords)
            ocr_text, ocr_confidence, ocr_language = ocr_processor.process_file(
                document.file_path, document.original_filename
            )
            
            # Re-run AI categorization with specified model (user-specific)
            ai_processor = self._get_ai_processor(document.user_id)
            ai_result = ai_processor.categorize_document(ocr_text, document.original_filename, ai_model)
            
            # Extract bill value from extracted_data
            extracted_data = ai_result.get('extracted_data', {})
            bill_value = None
            if extracted_data and 'amounts' in extracted_data and extracted_data['amounts']:
                try:
                    amount_str = extracted_data['amounts'][0].replace(',', '.')
                    bill_value = float(amount_str)
                except (ValueError, IndexError):
                    pass
            
            # Update document
            document.ocr_text = ocr_text
            document.ocr_confidence = ocr_confidence
            document.ocr_language = ocr_language
            document.category_id = ai_result.get('category_id')
            document.subcategory_id = ai_result.get('subcategory_id')
            document.ai_confidence = ai_result.get('confidence')
            document.extracted_data = json.dumps(extracted_data)
            document.bill_value = bill_value
            document.extracted_data = json.dumps(ai_result.get('extracted_data', {}))
            document.processed_at = datetime.utcnow()
            document.processing_error = None
            
            db.commit()
            
            return {
                'success': True,
                'document_id': document_id,
                'category_id': ai_result.get('category_id'),
                'subcategory_id': ai_result.get('subcategory_id'),
                'confidence': ai_result.get('confidence')
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        finally:
            db.close()
    
    def update_document_category(self, document_id: int, category_id: int, 
                                subcategory_id: Optional[int] = None):
        """Update document category (user correction) and trigger learning"""
        db = get_db()
        try:
            document = db.query(Document).filter_by(id=document_id).first()
            
            if not document:
                return {'success': False, 'error': 'Document not found'}
            
            # Update category
            old_category = document.category_id
            document.category_id = category_id
            document.subcategory_id = subcategory_id
            document.manually_categorized = True
            
            db.commit()
            
            # Learn from correction if category changed (user-specific)
            if old_category != category_id:
                ai_processor = self._get_ai_processor(document.user_id)
                ai_processor.learn_from_correction(
                    document_id, category_id, subcategory_id, document.ocr_text, document.user_id
                )
            
            return {'success': True}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        finally:
            db.close()
    
    def delete_document(self, document_id: int) -> Dict:
        """Delete a document"""
        db = get_db()
        try:
            document = db.query(Document).filter_by(id=document_id).first()
            
            if not document:
                return {'success': False, 'error': 'Document not found'}
            
            # Delete file
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            # Delete from database
            db.delete(document)
            db.commit()
            
            return {'success': True}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        finally:
            db.close()
