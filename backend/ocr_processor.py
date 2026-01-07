import os
import re
from typing import Optional, Tuple, List, Dict, Any
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import PyPDF2
import pdfplumber
from backend.config import config

# DOCX/DOC support (optional packages)
try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False

import subprocess
import shutil

class OCRProcessor:
    """Handle OCR processing for images and PDFs"""
    
    def __init__(self, user_passwords: Optional[List[str]] = None):
        # OCR engine: only Tesseract is supported
        # Keep engine flag for possible future engines
        self.ocr_engine = 'tesseract'
        
        # Tesseract setup
        self.tesseract_path = config.get('ocr.tesseract_path')
        if self.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        # Use only Slovenian for better character detection
        self.default_languages = ['slv']
        self.confidence_threshold = config.get('ocr.confidence_threshold', 60)
        
        # Tesseract config for better accuracy
        self.tesseract_config = '--psm 6 --oem 3'  # PSM 6: Uniform text block, OEM 3: Default
        
        # Store user-specific passwords for PDF decryption
        self.user_passwords = user_passwords or []
        
        # Only Tesseract is supported now (PaddleOCR removed to reduce memory usage)
        # Keep a simple engine flag for possible future engines
        self.ocr_engine = 'tesseract'
    
    def extract_language_from_filename(self, filename: str) -> Optional[str]:
        """Extract language code from filename (e.g., invoice_en.pdf -> en)"""
        # support pdf, images and DOCX (legacy .doc removed)
        pattern = r'_([a-z]{2,3})\.(pdf|png|jpg|jpeg|docx)$'
        match = re.search(pattern, filename.lower())
        return match.group(1) if match else None

    def process_docx(self, docx_path: str, language: Optional[str] = None) -> Tuple[str, float, str]:
        """
        Extract text from DOCX files using python-docx (only supported DOC format)
        Returns: (text, confidence, language_used)
        """
        if not language:
            language = 'slv'

        if DOCX_AVAILABLE:
            try:
                doc = DocxDocument(docx_path)
                paragraphs = [p.text for p in doc.paragraphs if p.text]
                text = '\n'.join(paragraphs)
                if text and text.strip():
                    return text.strip(), 100.0, language
                else:
                    raise Exception("DOCX file contains no extractable text")
            except Exception as e:
                raise Exception(f"DOCX extraction failed: {e}")

        raise Exception("DOCX extraction requires the 'python-docx' package (install with 'pip install python-docx')")


    

    
    def process_image(self, image_path: str, language: Optional[str] = None) -> Tuple[str, float, str]:
        """
        Process an image file with OCR
        Returns: (text, confidence, language_used)
        """
        if not language:
            language = 'slv'  # Use only Slovenian for better character detection
        
        # Use Tesseract for image OCR
        print("OCR: Using Tesseract")
        try:
            image = Image.open(image_path)
            
            # Perform OCR with detailed data for confidence
            ocr_data = pytesseract.image_to_data(
                image, 
                lang=language, 
                config=self.tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text
            text = pytesseract.image_to_string(
                image, 
                lang=language,
                config=self.tesseract_config
            )
            
            # Calculate average confidence
            confidences = [int(conf) for conf in ocr_data['conf'] if conf != '-1']
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return text.strip(), avg_confidence, language
        
        except Exception as e:
            raise Exception(f"OCR processing failed: {str(e)}")
    
    def process_pdf(self, pdf_path: str, language: Optional[str] = None) -> Tuple[str, float, str]:
        """
        Process a PDF file - try text extraction first, then OCR if needed
        Returns: (text, confidence, language_used)
        """
        if not language:
            language = 'slv'  # Use only Slovenian for better character detection
        
        # Try to extract text directly from PDF
        text = self._extract_text_from_pdf(pdf_path)
        
        if text and len(text.strip()) > 50:
            # PDF has extractable text
            return text.strip(), 100.0, language
        
        # PDF is image-based or has no text, perform OCR
        return self._ocr_pdf_images(pdf_path, language)
    
    def _extract_text_from_pdf(self, pdf_path: str, try_passwords: bool = True) -> str:
        """Extract text directly from PDF"""
        text = ""
        # Combine user passwords (higher priority) with global passwords
        passwords = []
        if try_passwords:
            passwords = self.user_passwords + config.get('pdf.decrypt_passwords', [])
        
        # Try with pdfplumber first (better formatting)
        try:
            with pdfplumber.open(pdf_path, password=passwords[0] if passwords else None) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception:
            pass
        
        # Fallback to PyPDF2
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Handle encrypted PDFs
                if pdf_reader.is_encrypted:
                    decrypted = False
                    for password in passwords:
                        try:
                            if pdf_reader.decrypt(password):
                                decrypted = True
                                break
                        except:
                            continue
                    
                    if not decrypted:
                        raise Exception("PDF is encrypted and could not be decrypted")
                
                # Extract text from all pages
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                return text
        except Exception as e:
            raise Exception(f"PDF text extraction failed: {str(e)}")
    
    def _ocr_pdf_images(self, pdf_path: str, language: str) -> Tuple[str, float, str]:
        """Convert PDF pages to images and perform OCR"""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            
            all_text = []
            all_confidences = []
            
            
            # Fallback to Tesseract
            all_text = []
            all_confidences = []
            
            for image in images:
                # Perform OCR on each page with config
                ocr_data = pytesseract.image_to_data(
                    image, 
                    lang=language, 
                    config=self.tesseract_config,
                    output_type=pytesseract.Output.DICT
                )
                page_text = pytesseract.image_to_string(
                    image, 
                    lang=language,
                    config=self.tesseract_config
                )
                
                all_text.append(page_text)
                
                # Calculate confidence for this page
                confidences = [int(conf) for conf in ocr_data['conf'] if conf != '-1']
                if confidences:
                    all_confidences.extend(confidences)
            
            # Combine results
            combined_text = '\n'.join(all_text)
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
            
            return combined_text.strip(), avg_confidence, language
        
        except Exception as e:
            raise Exception(f"PDF OCR failed: {str(e)}")
    
    def process_file(self, file_path: str, filename: str) -> Tuple[str, float, str]:
        """
        Process any supported file (auto-detect type)
        Returns: (text, confidence, language_used)
        """
        # Extract language from filename if present
        lang_from_filename = self.extract_language_from_filename(filename)
        language = lang_from_filename if lang_from_filename else None
        
        # Determine file type
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == '.pdf':
            return self.process_pdf(file_path, language)
        elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            return self.process_image(file_path, language)
        elif ext == '.docx':
            return self.process_docx(file_path, language)
        else:
            raise Exception(f"Unsupported file type: {ext}")
