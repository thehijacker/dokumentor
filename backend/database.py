import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from backend.config import config

Base = declarative_base()


class User(Base):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # User-specific settings
    pdf_passwords = Column(Text, nullable=True)  # JSON array of passwords for encrypted PDFs
    
    # Relationships
    documents = relationship('Document', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password: str):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check if password matches"""
        return check_password_hash(self.password_hash, password)
    
    # Flask-Login required methods
    def get_id(self):
        """Return user ID as string (required by Flask-Login)"""
        return str(self.id)
    
    @property
    def is_authenticated(self):
        """Return True if user is authenticated (required by Flask-Login)"""
        return True
    
    @property
    def is_anonymous(self):
        """Return False for regular users (required by Flask-Login)"""
        return False
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }


def slovenian_sort_key(text):
    """Generate sort key for Slovenian text (handles č, š, ž correctly)"""
    if not text:
        return ''
    replacements = {
        'č': 'c\x01',
        'Č': 'C\x01',
        'š': 's\x01',
        'Š': 'S\x01',
        'ž': 'z\x01',
        'Ž': 'Z\x01'
    }
    result = text.lower()
    for old, new in replacements.items():
        result = result.replace(old.lower(), new)
    return result


class Category(Base):
    """Category model for document organization"""
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User')
    subcategories = relationship('Subcategory', back_populates='category', cascade='all, delete-orphan')
    documents = relationship('Document', back_populates='category')
    
    def to_dict(self, include_subcategories=True):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }
        if include_subcategories:
            # Sort subcategories using Slovenian collation before serializing
            sorted_subs = sorted(self.subcategories, key=lambda s: slovenian_sort_key(s.name))
            data['subcategories'] = [sub.to_dict(include_category=False) for sub in sorted_subs]
        return data


class Subcategory(Base):
    """Subcategory model for detailed organization"""
    __tablename__ = 'subcategories'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User')
    category = relationship('Category', back_populates='subcategories')
    documents = relationship('Document', back_populates='subcategory')
    
    def to_dict(self, include_category=True):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }
        if include_category and self.category:
            data['category'] = {
                'id': self.category.id,
                'name': self.category.name
            }
        return data


class Document(Base):
    """Document model for storing file information"""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, image, etc.
    file_size = Column(Integer, nullable=False)  # in bytes
    file_hash = Column(String(64), nullable=True, index=True)  # SHA256 hash for duplicate detection
    
    # OCR and processing
    ocr_text = Column(Text, nullable=True)
    ocr_language = Column(String(10), nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    
    # Categorization
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    subcategory_id = Column(Integer, ForeignKey('subcategories.id'), nullable=True)
    ai_confidence = Column(Float, nullable=True)
    manually_categorized = Column(Boolean, default=False)
    
    # Metadata
    extracted_data = Column(Text, nullable=True)  # JSON string
    bill_value = Column(Float, nullable=True)  # Extracted bill/invoice value
    notes = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)  # Comma-separated
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Status
    is_processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='documents')
    category = relationship('Category', back_populates='documents')
    subcategory = relationship('Subcategory', back_populates='documents')
    learning_records = relationship('LearningRecord', back_populates='document', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'ocr_text': self.ocr_text,
            'ocr_language': self.ocr_language,
            'ocr_confidence': self.ocr_confidence,
            'category': self.category.to_dict(include_subcategories=False) if self.category else None,
            'subcategory': self.subcategory.to_dict(include_category=False) if self.subcategory else None,
            'ai_confidence': self.ai_confidence,
            'manually_categorized': self.manually_categorized,
            'extracted_data': self.extracted_data,
            'bill_value': self.bill_value,
            'notes': self.notes,
            'tags': self.tags.split(',') if self.tags else [],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'is_processed': self.is_processed,
            'processing_error': self.processing_error
        }


class LearningRecord(Base):
    """Learning records for AI improvement"""
    __tablename__ = 'learning_records'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    text_features = Column(Text, nullable=False)  # JSON string of features
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    subcategory_id = Column(Integer, ForeignKey('subcategories.id'), nullable=True)
    confidence = Column(Float, nullable=False)
    was_correct = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship('Document', back_populates='learning_records')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'category_id': self.category_id,
            'subcategory_id': self.subcategory_id,
            'confidence': self.confidence,
            'was_correct': self.was_correct,
            'created_at': self.created_at.isoformat()
        }


# Database session management
engine = None
SessionLocal = None


def init_db():
    """Initialize database"""
    global engine, SessionLocal
    
    db_path = config.get('database.path', './data/documents.db')
    db_dir = os.path.dirname(db_path)
    
    # Create directory if it doesn't exist
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    # Create engine
    engine = create_engine(f'sqlite:///{db_path}', echo=config.get('app.debug', False))
    SessionLocal = sessionmaker(bind=engine)
    
    # Create tables
    Base.metadata.create_all(engine)
    
    # Optionally initialize predefined categories (disabled by default)
    session = SessionLocal()
    try:
        initialize_predefined = config.get('categories.initialize_predefined', False)
        if initialize_predefined and session.query(Category).count() == 0:
            predefined = config.get('categories.predefined', [])
            for cat_data in predefined:
                category = Category(
                    name=cat_data['name'],
                    description=f"Predefined category: {cat_data['name']}"
                )
                session.add(category)
                session.flush()

                for subcat_name in cat_data.get('subcategories', []):
                    subcategory = Subcategory(
                        name=subcat_name,
                        category_id=category.id,
                        description=f"Predefined subcategory: {subcat_name}"
                    )
                    session.add(subcategory)

            session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error initializing categories: {e}")
    finally:
        session.close()


def get_db():
    """Get database session"""
    if SessionLocal is None:
        init_db()
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Session will be closed by caller
