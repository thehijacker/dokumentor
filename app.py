import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from werkzeug.utils import secure_filename
from backend.config import config
from backend.database import init_db, get_db, User, Document, Category, Subcategory
from backend.document_processor import DocumentProcessor
from backend.watch_folder import WatchFolderService
import json

def slovenian_sort_key(text):
    """Generate sort key for Slovenian text (handles č, š, ž correctly)"""
    if not text:
        return ''
    # Slovenian alphabet order: a,b,c,č,d,e,f,g,h,i,j,k,l,m,n,o,p,r,s,š,t,u,v,z,ž
    replacements = {
        'č': 'c\x01',  # After c
        'Č': 'C\x01',
        'š': 's\x01',  # After s
        'Š': 'S\x01',
        'ž': 'z\x01',  # After z
        'Ž': 'Z\x01'
    }
    result = text.lower()
    for old, new in replacements.items():
        result = result.replace(old.lower(), new)
    return result

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = config.get('app.secret_key', 'change-this-secret-key')
app.config['MAX_CONTENT_LENGTH'] = config.get('storage.max_file_size', 52428800)  # 50MB

# Session cookie settings for HTTPS
secure_cookies = config.get('app.secure_cookies', True)
app.config['SESSION_COOKIE_SECURE'] = secure_cookies  # Only send over HTTPS when enabled
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JS access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['REMEMBER_COOKIE_SECURE'] = secure_cookies  # Flask-Login remember me cookie
app.logger.info("Secure cookies enabled: %s", secure_cookies)

# CORS
CORS(app)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize processors
document_processor = DocumentProcessor()
watch_folder_service = WatchFolderService()

# Setup logging
log_dir = os.path.dirname(config.get('logging.file', './logs/app.log'))
if log_dir:
    os.makedirs(log_dir, exist_ok=True)

handler = RotatingFileHandler(
    config.get('logging.file', './logs/app.log'),
    maxBytes=config.get('logging.max_bytes', 10485760),
    backupCount=config.get('logging.backup_count', 5)
)
handler.setLevel(getattr(logging, config.get('logging.level', 'INFO')))
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(getattr(logging, config.get('logging.level', 'INFO')))


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    try:
        return db.query(User).filter_by(id=int(user_id)).first()
    finally:
        db.close()


# ============== Web Routes ==============

@app.route('/')
def index():
    """Main page"""
    if current_user.is_authenticated:
        return render_template('index.html')
    return redirect(url_for('login'))


@app.route('/sw.js')
def service_worker():
    """Serve service worker from root for proper scope"""
    return send_file('static/sw.js', mimetype='application/javascript')


@app.route('/login')
def login():
    """Login page"""
    return render_template('login.html')


@app.route('/register')
def register():
    """Registration page"""
    if not config.get('auth.enable_registration', True):
        return jsonify({'error': 'Registration is disabled'}), 403
    return render_template('register.html')


# ============== API Routes ==============

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Login API"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    db = get_db()
    try:
        user = db.query(User).filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                return jsonify({'error': 'Account is disabled'}), 403
            
            login_user(user)
            return jsonify({
                'success': True,
                'user': user.to_dict()
            })
        
        return jsonify({'error': 'Invalid credentials'}), 401
    finally:
        db.close()


@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """Registration API"""
    if not config.get('auth.enable_registration', True):
        return jsonify({'error': 'Registration is disabled'}), 403
    
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'error': 'All fields required'}), 400
    
    db = get_db()
    try:
        # Check if user exists
        if db.query(User).filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if db.query(User).filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        login_user(user)
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
    finally:
        db.close()


@app.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    """Logout API"""
    logout_user()
    return jsonify({'success': True})


@app.route('/api/auth/me')
@login_required
def api_me():
    """Get current user"""
    db = get_db()
    try:
        user = db.query(User).filter_by(id=current_user.id).first()
        return jsonify(user.to_dict())
    finally:
        db.close()


@app.route('/api/user/settings/pdf-passwords', methods=['GET'])
@login_required
def api_get_pdf_passwords():
    """Get user's PDF passwords"""
    db = get_db()
    try:
        user = db.query(User).filter_by(id=current_user.id).first()
        if user and user.pdf_passwords:
            try:
                passwords = json.loads(user.pdf_passwords)
                return jsonify({'passwords': passwords if isinstance(passwords, list) else []})
            except:
                return jsonify({'passwords': []})
        return jsonify({'passwords': []})
    finally:
        db.close()


@app.route('/api/user/settings/pdf-passwords', methods=['POST'])
@login_required
def api_update_pdf_passwords():
    """Update user's PDF passwords"""
    db = get_db()
    try:
        data = request.get_json()
        passwords = data.get('passwords', [])
        
        # Validate input
        if not isinstance(passwords, list):
            return jsonify({'success': False, 'error': 'Passwords must be a list'}), 400
        
        # Filter empty strings and validate
        passwords = [p.strip() for p in passwords if p and p.strip()]
        
        user = db.query(User).filter_by(id=current_user.id).first()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user.pdf_passwords = json.dumps(passwords)
        db.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Updated {len(passwords)} PDF password(s)',
            'passwords': passwords
        })
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/categories')
@login_required
def api_categories():
    """Get all categories with subcategories for current user"""
    db = get_db()
    try:
        categories = db.query(Category).filter_by(user_id=current_user.id).all()
        # Sort with Slovenian collation
        categories_sorted = sorted(categories, key=lambda c: slovenian_sort_key(c.name))
        return jsonify([cat.to_dict() for cat in categories_sorted])
    finally:
        db.close()


@app.route('/api/categories/<int:category_id>/subcategories')
@login_required
def api_subcategories(category_id):
    """Get subcategories for a category (user-specific)"""
    db = get_db()
    try:
        subcategories = db.query(Subcategory).filter_by(
            category_id=category_id,
            user_id=current_user.id
        ).all()
        # Sort with Slovenian collation
        subcategories_sorted = sorted(subcategories, key=lambda s: slovenian_sort_key(s.name))
        return jsonify([sub.to_dict(include_category=False) for sub in subcategories_sorted])
    finally:
        db.close()


@app.route('/api/categories', methods=['POST'])
@login_required
def api_create_category():
    """Create a new category for current user"""
    db = get_db()
    try:
        data = request.json
        
        # Check if category already exists for this user
        existing = db.query(Category).filter_by(
            name=data['name'],
            user_id=current_user.id
        ).first()
        if existing:
            return jsonify({'error': 'Category already exists'}), 400
        
        category = Category(
            name=data['name'],
            description=data.get('description', ''),
            user_id=current_user.id
        )
        db.add(category)
        db.commit()
        
        return jsonify(category.to_dict()), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/categories/<int:category_id>', methods=['PUT'])
@login_required
def api_update_category(category_id):
    """Update a category (must be owned by user)"""
    db = get_db()
    try:
        category = db.query(Category).filter_by(
            id=category_id,
            user_id=current_user.id
        ).first()
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        data = request.json
        category.name = data.get('name', category.name)
        category.description = data.get('description', category.description)
        db.commit()
        
        return jsonify(category.to_dict())
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
@login_required
def api_delete_category(category_id):
    """Delete a category and all its subcategories (must be owned by user)"""
    db = get_db()
    try:
        category = db.query(Category).filter_by(
            id=category_id,
            user_id=current_user.id
        ).first()
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        # Check if category has documents
        doc_count = db.query(Document).filter_by(category_id=category_id).count()
        if doc_count > 0:
            return jsonify({'error': f'Cannot delete category with {doc_count} documents'}), 400
        
        db.delete(category)
        db.commit()
        
        return jsonify({'message': 'Category deleted successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/subcategories', methods=['POST'])
@login_required
def api_create_subcategory():
    """Create a new subcategory for current user"""
    db = get_db()
    try:
        data = request.json
        
        # Check if parent category exists and is owned by user
        category = db.query(Category).filter_by(
            id=data['category_id'],
            user_id=current_user.id
        ).first()
        if not category:
            return jsonify({'error': 'Parent category not found'}), 404
        
        # Check if subcategory already exists for this user
        existing = db.query(Subcategory).filter_by(
            category_id=data['category_id'],
            name=data['name'],
            user_id=current_user.id
        ).first()
        if existing:
            return jsonify({'error': 'Subcategory already exists'}), 400
        
        subcategory = Subcategory(
            name=data['name'],
            category_id=data['category_id'],
            user_id=current_user.id
        )
        db.add(subcategory)
        db.commit()
        
        return jsonify(subcategory.to_dict()), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/subcategories/<int:subcategory_id>', methods=['PUT'])
@login_required
def api_update_subcategory(subcategory_id):
    """Update a subcategory (must be owned by user)"""
    db = get_db()
    try:
        subcategory = db.query(Subcategory).filter_by(
            id=subcategory_id,
            user_id=current_user.id
        ).first()
        if not subcategory:
            return jsonify({'error': 'Subcategory not found'}), 404
        
        data = request.json
        subcategory.name = data.get('name', subcategory.name)
        db.commit()
        
        return jsonify(subcategory.to_dict())
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/subcategories/<int:subcategory_id>', methods=['DELETE'])
@login_required
def api_delete_subcategory(subcategory_id):
    """Delete a subcategory (must be owned by user)"""
    db = get_db()
    try:
        subcategory = db.query(Subcategory).filter_by(
            id=subcategory_id,
            user_id=current_user.id
        ).first()
        if not subcategory:
            return jsonify({'error': 'Subcategory not found'}), 404
        
        # Check if subcategory has documents
        doc_count = db.query(Document).filter_by(subcategory_id=subcategory_id).count()
        if doc_count > 0:
            return jsonify({'error': f'Cannot delete subcategory with {doc_count} documents'}), 400
        
        db.delete(subcategory)
        db.commit()
        
        return jsonify({'message': 'Subcategory deleted successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/documents', methods=['GET'])
@login_required
def api_documents():
    """Get all documents for current user"""
    db = get_db()
    try:
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Filters
        category_id = request.args.get('category_id', type=int)
        subcategory_id = request.args.get('subcategory_id', type=int)
        search = request.args.get('search', '')
        
        # Sorting
        sort_by = request.args.get('sort_by', 'filename')
        sort_order = request.args.get('sort_order', 'asc')
        
        query = db.query(Document).filter_by(user_id=current_user.id)
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if subcategory_id:
            query = query.filter_by(subcategory_id=subcategory_id)
        
        if search:
            # Case-insensitive search with proper Unicode handling
            # Search in filename, OCR text, notes, category name, and subcategory name
            search_pattern = f"%{search}%"
            
            # Join with category and subcategory for name searching
            query = query.outerjoin(Category, Document.category_id == Category.id)
            query = query.outerjoin(Subcategory, Document.subcategory_id == Subcategory.id)
            
            query = query.filter(
                (Document.original_filename.ilike(search_pattern)) |
                (Document.ocr_text.ilike(search_pattern)) |
                (Document.notes.ilike(search_pattern)) |
                (Category.name.ilike(search_pattern)) |
                (Subcategory.name.ilike(search_pattern))
            )
        else:
            # If no search, still need joins for sorting by category/subcategory names
            if sort_by in ['category', 'subcategory']:
                query = query.outerjoin(Category, Document.category_id == Category.id)
                query = query.outerjoin(Subcategory, Document.subcategory_id == Subcategory.id)
        
        # Apply sorting
        if sort_by == 'filename':
            order_column = Document.original_filename
        elif sort_by == 'category':
            order_column = Category.name
        elif sort_by == 'subcategory':
            order_column = Subcategory.name
        elif sort_by == 'bill_value':
            order_column = Document.bill_value
        elif sort_by == 'confidence':
            order_column = Document.ai_confidence
        elif sort_by == 'uploaded':
            order_column = Document.created_at
        else:
            order_column = Document.original_filename
        
        if sort_order == 'desc':
            query = query.order_by(order_column.desc().nullslast())
        else:
            query = query.order_by(order_column.asc().nullslast())
        
        # Paginate
        total = query.count()
        documents = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'documents': [doc.to_dict() for doc in documents],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        })
    finally:
        db.close()


@app.route('/api/documents/<int:document_id>', methods=['GET'])
@login_required
def api_document(document_id):
    """Get a specific document"""
    db = get_db()
    try:
        document = db.query(Document).filter_by(
            id=document_id,
            user_id=current_user.id
        ).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        return jsonify(document.to_dict())
    finally:
        db.close()


@app.route('/api/documents/upload', methods=['POST'])
@login_required
def api_upload():
    """Upload and process a document"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type
    allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.docx'}
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext not in allowed_extensions:
        return jsonify({'error': f'File type {ext} not supported'}), 400
    
    try:
        # Save temporary file
        temp_dir = './uploads'
        os.makedirs(temp_dir, exist_ok=True)
        
        filename = secure_filename(file.filename)
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)
        
        # Calculate file hash for duplicate detection
        import hashlib
        with open(temp_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Check for duplicate
        db = get_db()
        existing_doc = db.query(Document).filter_by(
            user_id=current_user.id,
            file_hash=file_hash
        ).first()
        
        if existing_doc:
            os.remove(temp_path)
            db.close()
            return jsonify({
                'error': 'Duplicate file detected',
                'duplicate_of': existing_doc.id,
                'original_filename': existing_doc.original_filename
            }), 409
        
        db.close()
        
        # Get AI model preference from form data
        ai_model = request.form.get('ai_model', None)
        
        # Get user's PDF passwords
        pdf_passwords = []
        if current_user.pdf_passwords:
            try:
                pdf_passwords = json.loads(current_user.pdf_passwords)
            except:
                pass
        
        # Process document with user's passwords
        result = document_processor.process_file(
            temp_path, 
            current_user.id, 
            filename, 
            file_hash, 
            ai_model,
            pdf_passwords=pdf_passwords
        )
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        if result['success']:
            return jsonify({
                'success': True,
                'document_id': result['document_id'],
                'category_id': result.get('category_id'),
                'subcategory_id': result.get('subcategory_id'),
                'confidence': result.get('confidence')
            })
        else:
            return jsonify({'error': result.get('error')}), 500
    
    except Exception as e:
        app.logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/documents/<int:document_id>/update', methods=['PUT'])
@login_required
def api_update_document(document_id):
    """Update document metadata"""
    db = get_db()
    try:
        document = db.query(Document).filter_by(
            id=document_id,
            user_id=current_user.id
        ).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        data = request.json
        
        # Update allowed fields
        if 'category_id' in data:
            old_category = document.category_id
            old_subcategory = document.subcategory_id
            was_manually_categorized = document.manually_categorized
            
            document.category_id = data['category_id']
            document.subcategory_id = data.get('subcategory_id')
            document.manually_categorized = True
            
            # Trigger learning if:
            # 1. Category changed, OR
            # 2. Subcategory changed, OR
            # 3. First time manually categorizing (learning from AI's initial prediction)
            if (old_category != data['category_id'] or 
                old_subcategory != data.get('subcategory_id') or
                not was_manually_categorized):
                # Get user-specific AI processor and learn from correction
                ai_processor = document_processor._get_ai_processor(current_user.id)
                ai_processor.learn_from_correction(
                    document_id,
                    data['category_id'],
                    data.get('subcategory_id'),
                    document.ocr_text,
                    current_user.id
                )
        
        if 'notes' in data:
            document.notes = data['notes']
        
        if 'bill_value' in data:
            document.bill_value = data['bill_value']
        
        if 'original_filename' in data:
            document.original_filename = data['original_filename']
        
        if 'tags' in data:
            if isinstance(data['tags'], list):
                document.tags = ','.join(data['tags'])
            else:
                document.tags = data['tags']
        
        db.commit()
        
        return jsonify({
            'success': True,
            'document': document.to_dict()
        })
    finally:
        db.close()


@app.route('/api/documents/<int:document_id>/reprocess', methods=['POST'])
@login_required
def api_reprocess_document(document_id):
    """Reprocess a document"""
    db = get_db()
    try:
        document = db.query(Document).filter_by(
            id=document_id,
            user_id=current_user.id
        ).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Get AI model from request body
        data = request.get_json() or {}
        ai_model = data.get('ai_model', None)
        
        result = document_processor.reprocess_document(document_id, ai_model)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result.get('error')}), 500
    finally:
        db.close()


@app.route('/api/documents/<int:document_id>/delete', methods=['DELETE'])
@login_required
def api_delete_document(document_id):
    """Delete a document"""
    db = get_db()
    try:
        document = db.query(Document).filter_by(
            id=document_id,
            user_id=current_user.id
        ).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        result = document_processor.delete_document(document_id)
        
        if result['success']:
            return jsonify({'success': True})
        else:
            return jsonify({'error': result.get('error')}), 500
    finally:
        db.close()


@app.route('/api/documents/<int:document_id>/download')
@login_required
def api_download_document(document_id):
    """Download a document file"""
    db = get_db()
    try:
        document = db.query(Document).filter_by(
            id=document_id,
            user_id=current_user.id
        ).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        if not os.path.exists(document.file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            document.file_path,
            as_attachment=True,
            download_name=document.original_filename
        )
    finally:
        db.close()


@app.route('/api/documents/<int:document_id>/preview')
@login_required
def api_preview_document(document_id):
    """Preview a document file inline in browser"""
    import PyPDF2
    from io import BytesIO
    
    db = get_db()
    try:
        document = db.query(Document).filter_by(
            id=document_id,
            user_id=current_user.id
        ).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        if not os.path.exists(document.file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Determine MIME type
        mime_types = {
            'pdf': 'application/pdf',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'bmp': 'image/bmp',
            'tiff': 'image/tiff',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        mime_type = mime_types.get(document.file_type.lower(), 'application/octet-stream')
        
        # Handle encrypted PDFs
        if document.file_type.lower() == 'pdf':
            try:
                with open(document.file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    # Check if PDF is encrypted
                    if pdf_reader.is_encrypted:
                        # Build password list from multiple sources
                        passwords = []
                        
                        # 1. User-specific passwords (highest priority)
                        if current_user and current_user.pdf_passwords:
                            try:
                                user_passwords = json.loads(current_user.pdf_passwords)
                                if isinstance(user_passwords, list):
                                    passwords.extend(user_passwords)
                            except:
                                pass
                        
                        # 2. Password from document extracted_data
                        if document.extracted_data:
                            try:
                                extracted = json.loads(document.extracted_data)
                                if 'passwords' in extracted and extracted['passwords']:
                                    passwords.extend(extracted['passwords'])
                            except:
                                pass
                        
                        # 3. Global passwords from config (lowest priority)
                        global_passwords = config.get('pdf.decrypt_passwords', [])
                        passwords.extend(global_passwords)
                        
                        # Remove duplicates while preserving order
                        seen = set()
                        unique_passwords = []
                        for pwd in passwords:
                            if pwd and pwd not in seen:
                                seen.add(pwd)
                                unique_passwords.append(pwd)
                        
                        print(f"PDF Preview: Trying {len(unique_passwords)} passwords for document {document_id}")
                        
                        # Try each password
                        decrypted = False
                        for i, password in enumerate(unique_passwords):
                            try:
                                result = pdf_reader.decrypt(password)
                                # decrypt() returns 0 for failure, 1 for success with user password, 2 for success with owner password
                                if result > 0:
                                    decrypted = True
                                    print(f"PDF Preview: Successfully decrypted with password #{i+1}")
                                    break
                            except Exception as e:
                                print(f"PDF Preview: Password #{i+1} failed: {e}")
                                continue
                        
                        if decrypted:
                            # Create a new PDF without encryption
                            pdf_writer = PyPDF2.PdfWriter()
                            for page in pdf_reader.pages:
                                pdf_writer.add_page(page)
                            
                            # Write to BytesIO
                            output = BytesIO()
                            pdf_writer.write(output)
                            output.seek(0)
                            
                            return send_file(
                                output,
                                mimetype='application/pdf',
                                as_attachment=False
                            )
                        else:
                            print(f"PDF Preview: All {len(unique_passwords)} passwords failed")
            except Exception as e:
                print(f"PDF decryption failed: {e}")
                # Fall through to send original file
        
        return send_file(
            document.file_path,
            mimetype=mime_type,
            as_attachment=False
        )
    finally:
        db.close()


@app.route('/api/stats')
@login_required
def api_stats():
    """Get user statistics"""
    db = get_db()
    try:
        total_docs = db.query(Document).filter_by(user_id=current_user.id).count()
        processed_docs = db.query(Document).filter_by(
            user_id=current_user.id,
            is_processed=True
        ).count()
        
        # Documents by category (only user's categories)
        categories = db.query(Category).filter_by(user_id=current_user.id).all()
        by_category = {}
        for cat in categories:
            count = db.query(Document).filter_by(
                user_id=current_user.id,
                category_id=cat.id
            ).count()
            by_category[cat.name] = count
        
        return jsonify({
            'total_documents': total_docs,
            'processed_documents': processed_docs,
            'by_category': by_category
        })
    finally:
        db.close()


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'version': config.get('app.version', '1.0.0')})


@app.route('/api/config')
def api_config():
    """Get public configuration"""
    return jsonify({
        'registration_enabled': config.get('auth.enable_registration', True),
        'app_name': config.get('app.name', 'Dokumentor')
    })


# Inject common template variables like app name and version
@app.context_processor
def inject_app_info():
    try:
        import backend as _backend
        version = getattr(_backend, '__version__', None)
    except Exception:
        version = None

    return {
        'app_name': config.get('app.name', 'Dokumentor'),
        'app_version': version or config.get('app.version', '1.0.0')
    }


if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Start watch folder service
    try:
        watch_folder_service.start(document_processor)
    except Exception as e:
        app.logger.error(f"Failed to start watch folder service: {e}")
    
    # Run application
    host = config.get('server.host', '0.0.0.0')
    port = config.get('server.port', 5000)
    debug = config.get('app.debug', False)
    
    app.logger.info(f"Starting Dokumentor on {host}:{port}")
    
    try:
        app.run(host=host, port=port, debug=debug)
    finally:
        watch_folder_service.stop()
