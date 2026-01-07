import os
import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import joblib
from backend.config import config
from backend.database import get_db, LearningRecord, Category, Subcategory, Document


class AIProcessor:
    """Handle AI-based categorization and learning"""
    
    def __init__(self, user_id: int = None):
        self.user_id = user_id
        self.provider = config.get('ai.provider', 'internal')
        self.model_name = config.get('ai.model', 'internal')
        self.confidence_threshold = config.get('ai.confidence_threshold', 0.7)
        # Threshold for accepting subcategory predictions (0.0 = always accept highest-prob subcategory)
        self.subcategory_confidence_threshold = config.get('ai.subcategory_confidence_threshold', 0.0)
        self.learning_enabled = config.get('ai.learning_enabled', True)
        
        # Internal ML model
        self.category_model = None
        self.subcategory_models = {}
        self.model_path = './data/models'
        
        abs_path = os.path.abspath(self.model_path)
        print(f"AI: Model path set to: {abs_path}")
        os.makedirs(self.model_path, exist_ok=True)
        print(f"AI: Model directory exists: {os.path.exists(self.model_path)}")
        
        if self.provider == 'internal' and user_id:
            self._load_models()
    
    def _get_model_filename(self, model_type: str, category_id: int = None) -> str:
        """Get user-specific model filename"""
        if not self.user_id:
            # Fallback to global models if no user_id
            if model_type == 'category':
                return 'category_model.pkl'
            else:
                return f'subcategory_{category_id}_model.pkl'
        
        # User-specific models
        if model_type == 'category':
            return f'user_{self.user_id}_category_model.pkl'
        else:
            return f'user_{self.user_id}_subcategory_{category_id}_model.pkl'
    
    def categorize_document(self, text: str, filename: str, preferred_model: str = None) -> Dict:
        """
        Categorize a document using AI
        Returns: {
            'category_id': int,
            'subcategory_id': int,
            'confidence': float,
            'extracted_data': dict,
            'model_used': str
        }
        """
        # Use preferred model if specified, otherwise use internal (pretrained)
        model = preferred_model or 'internal'
        
        # Try the primary model
        if self.provider == 'internal' or model == 'internal':
            result = self._categorize_internal(text, filename)
        elif model == 'openai':
            result = self._categorize_openai(text, filename)
        elif model == 'ollama':
            result = self._categorize_ollama(text, filename)
        else:
            # Default to internal if unknown model specified
            result = self._categorize_internal(text, filename)
        
        # Automatic fallback to Ollama if confidence is low and Ollama is available
        if result.get('confidence', 0) < 0.5 and model != 'ollama':
            ollama_url = config.get('ai.ollama_url')
            if ollama_url:
                print(f"AI: Low confidence ({result.get('confidence', 0):.2f}), trying Ollama fallback...")
                try:
                    ollama_result = self._categorize_ollama(text, filename)
                    if ollama_result.get('confidence', 0) > result.get('confidence', 0):
                        print(f"AI: Ollama provided better confidence ({ollama_result.get('confidence', 0):.2f})")
                        ollama_result['model_used'] = 'ollama (fallback)'
                        return ollama_result
                except Exception as e:
                    print(f"AI: Ollama fallback failed: {e}")
        
        result['model_used'] = model
        return result
    
    def _categorize_simple(self, text: str, filename: str) -> Dict:
        """Simple keyword-based categorization"""
        print(f"AI: Using simple categorization for {filename}")
        print(f"AI: Text length: {len(text)} characters")
        
        db = get_db()
        categories = db.query(Category).all()
        
        text_lower = text.lower()
        filename_lower = filename.lower()
        combined = f"{text_lower} {filename_lower}"
        
        # Define keyword patterns for categories
        patterns = {
            'Monthly Costs': [
                r'electricity|power|energy|elektrika',
                r'water|voda',
                r'internet|telecommunications',
                r'mobile|phone|telefon',
                r'gas|plin'
            ],
            'Shops': [
                r'ikea',
                r'lidl',
                r'hofer',
                r'mercator',
                r'spar',
                r'shop|store|trgovina'
            ],
            'Medical': [
                r'doctor|physician|zdravnik',
                r'hospital|bolnica',
                r'prescription|recept',
                r'pharmacy|lekarna'
            ],
            'Automotive': [
                r'fuel|petrol|gas|gorivo',
                r'maintenance|service|servis',
                r'insurance|zavarovanje',
                r'car|vehicle|avto'
            ]
        }
        
        best_match = None
        best_score = 0
        
        for category in categories:
            if category.name in patterns:
                score = 0
                for pattern in patterns[category.name]:
                    if re.search(pattern, combined):
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_match = category
        
        if best_match and best_score > 0:
            confidence = min(best_score * 0.3, 0.9)  # Cap at 0.9
            
            # Try to find subcategory
            subcategory = self._find_subcategory_simple(combined, best_match)
            
            print(f"AI: Matched category '{best_match.name}' with confidence {confidence}")
            
            return {
                'category_id': best_match.id,
                'subcategory_id': subcategory.id if subcategory else None,
                'confidence': confidence,
                'extracted_data': self._extract_data_simple(text)
            }
        
        # Default to "Other" category
        other_cat = db.query(Category).filter_by(name='Other').first()
        if other_cat:
            print(f"AI: No match found, defaulting to 'Other' category")
            return {
                'category_id': other_cat.id,
                'subcategory_id': None,
                'confidence': 0.3,
                'extracted_data': self._extract_data_simple(text)
            }
        
        db.close()
        return {'category_id': None, 'subcategory_id': None, 'confidence': 0.0, 'extracted_data': {}}
    
    def _find_subcategory_simple(self, text: str, category: Category) -> Optional[Subcategory]:
        """Find best matching subcategory using keywords"""
        best_match = None
        best_score = 0
        
        for subcategory in category.subcategories:
            # Check if subcategory name appears in text
            if subcategory.name.lower() in text:
                score = len(subcategory.name)
                if score > best_score:
                    best_score = score
                    best_match = subcategory
        
        return best_match
    
    def _extract_data_simple(self, text: str) -> Dict:
        """Extract structured data from text (amounts, dates, etc.)"""
        data = {}
        
        # Extract amounts (supports € and $)
        amounts = re.findall(r'(?:€|EUR|\$|USD)\s*([0-9]+[.,][0-9]{2})|([0-9]+[.,][0-9]{2})\s*(?:€|EUR|\$|USD)', text)
        if amounts:
            data['amounts'] = [a[0] or a[1] for a in amounts]
        
        # Extract dates
        dates = re.findall(r'\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b', text)
        if dates:
            data['dates'] = dates
        
        # Extract invoice/bill numbers
        invoice_numbers = re.findall(r'(?:invoice|bill|račun|št)[:\s#]*([A-Z0-9-]+)', text, re.IGNORECASE)
        if invoice_numbers:
            data['invoice_numbers'] = invoice_numbers
        
        return data
    
    def _categorize_internal(self, text: str, filename: str) -> Dict:
        """Use internal ML model for categorization"""
        if self.category_model is None:
            print(f"AI: No trained model found, returning low confidence result")
            # Return low confidence to trigger Ollama fallback
            db = get_db()
            other_cat = db.query(Category).filter_by(name='Other').first()
            db.close()
            return {
                'category_id': other_cat.id if other_cat else None,
                'subcategory_id': None,
                'confidence': 0.0,
                'extracted_data': self._extract_data_simple(text)
            }
        
        print(f"AI: Using trained ML model for {filename}")
        
        try:
            # Predict category
            probabilities = self.category_model.predict_proba([text])[0]
            max_prob_idx = np.argmax(probabilities)
            confidence = probabilities[max_prob_idx]
            category_id = int(self.category_model.classes_[max_prob_idx])
            
            # Get category name for logging
            db = get_db()
            category = db.get(Category, category_id)
            category_name = category.name if category else f"ID:{category_id}"
            print(f"AI ML: Predicted category '{category_name}' with confidence {confidence:.2f}")
            
            # Predict subcategory if model exists
            subcategory_id = None
            subcategory_confidence = 0.0
            
            if category_id in self.subcategory_models:
                print(f"AI ML: Found subcategory model for category {category_id}")
                sub_probs = self.subcategory_models[category_id].predict_proba([text])[0]
                sub_max_idx = np.argmax(sub_probs)
                subcategory_confidence = sub_probs[sub_max_idx]
                
                # Use configured threshold for accepting subcategory predictions
                if subcategory_confidence >= self.subcategory_confidence_threshold:
                    subcategory_id = int(self.subcategory_models[category_id].classes_[sub_max_idx])
                    subcategory = db.get(Subcategory, subcategory_id)
                    subcategory_name = subcategory.name if subcategory else f"ID:{subcategory_id}"
                    print(f"AI ML: Predicted subcategory '{subcategory_name}' with confidence {subcategory_confidence:.2f} (threshold {self.subcategory_confidence_threshold:.2f})")
                else:
                    # Log the best guess but do not assign when below threshold
                    predicted_id = int(self.subcategory_models[category_id].classes_[sub_max_idx])
                    subcategory = db.get(Subcategory, predicted_id)
                    sub_name = subcategory.name if subcategory else f"ID:{predicted_id}"
                    print(f"AI ML: Best subcategory guess '{sub_name}' has confidence {subcategory_confidence:.2f} which is below threshold {self.subcategory_confidence_threshold:.2f} - not assigning")
            else:
                print(f"AI ML: No subcategory model available for category {category_id}")
                # If there is only one subcategory observed for this user+category in learning records,
                # auto-assign that subcategory (useful when user only ever had a single subcategory)
                assigned = False
                if self.user_id:
                    try:
                        db2 = get_db()
                        rows = db2.query(LearningRecord.subcategory_id).filter_by(user_id=self.user_id, category_id=category_id).distinct().all()
                        unique_subcats = [r[0] for r in rows if r[0] is not None]
                        # If learning records don't show a single subcategory, check existing documents metadata
                        if not unique_subcats:
                            doc_rows = db2.query(Document.subcategory_id).filter_by(user_id=self.user_id, category_id=category_id).distinct().all()
                            unique_subcats = [r[0] for r in doc_rows if r[0] is not None]
                        db2.close()

                        if len(set(unique_subcats)) == 1 and unique_subcats:
                            subcategory_id = unique_subcats[0]
                            try:
                                subcategory = db.get(Subcategory, subcategory_id)
                                subcategory_name = subcategory.name if subcategory else f"ID:{subcategory_id}"
                            except Exception:
                                subcategory_name = f"ID:{subcategory_id}"
                            print(f"AI ML: Only one subcategory '{subcategory_name}' seen for user {self.user_id} and category {category_id}; auto-assigning")
                            subcategory_confidence = 1.0
                            assigned = True
                    except Exception as e:
                        print(f"AI ML: Checking for single subcategory failed: {e}")
                if not assigned:
                    print(f"AI ML: No subcategory could be determined for category {category_id}")
            
            db.close()
            
            return {
                'category_id': category_id,
                'subcategory_id': subcategory_id,
                'confidence': float(confidence),
                'extracted_data': self._extract_data_simple(text)
            }
        except Exception as e:
            print(f"Internal model prediction failed: {e}")
            import traceback
            traceback.print_exc()
            return self._categorize_simple(text, filename)
    
    def _categorize_openai(self, text: str, filename: str) -> Dict:
        """Use OpenAI API for categorization"""
        try:
            import openai
            openai.api_key = config.get('ai.openai_api_key')
            
            db = get_db()
            categories = db.query(Category).all()
            cat_list = [f"{c.id}: {c.name}" for c in categories]
            
            prompt = f"""Analyze this document and categorize it.
            
Available categories:
{chr(10).join(cat_list)}

Document filename: {filename}
Document text: {text[:2000]}

Respond with JSON: {{"category_id": <id>, "subcategory": "<name or null>", "confidence": <0-1>, "extracted_data": {{"amounts": [], "dates": [], "description": ""}}}}
"""
            
            response = openai.ChatCompletion.create(
                model=config.get('ai.openai_model', 'gpt-3.5-turbo'),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            db.close()
            return result
        
        except Exception as e:
            print(f"OpenAI categorization failed: {e}")
            return self._categorize_simple(text, filename)
    
    def _categorize_ollama(self, text: str, filename: str) -> Dict:
        """Use Ollama for categorization"""
        try:
            import requests
            
            db = get_db()
            categories = db.query(Category).all()
            cat_list = [f"{c.id}: {c.name}" for c in categories]
            
            prompt = f"""Analyze this document and categorize it.
            
Available categories:
{chr(10).join(cat_list)}

Document filename: {filename}
Document text: {text[:2000]}

Respond with JSON only: {{"category_id": <id>, "subcategory": "<name or null>", "confidence": <0-1>}}
"""
            
            response = requests.post(
                f"{config.get('ai.ollama_url')}/api/generate",
                json={
                    "model": config.get('ai.ollama_model', 'llama2'),
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            response_data = response.json()
            print(f"AI: Ollama raw response: {response_data}")
            
            # Parse the response text which contains JSON
            if 'response' in response_data:
                result = json.loads(response_data['response'])
            else:
                raise ValueError(f"No 'response' field in Ollama output: {response_data}")
            
            result['extracted_data'] = self._extract_data_simple(text)
            db.close()
            return result
        
        except Exception as e:
            print(f"Ollama categorization failed: {e}")
            # Return low confidence result instead of falling back to simple
            db = get_db()
            other_cat = db.query(Category).filter_by(name='Other').first()
            db.close()
            return {
                'category_id': other_cat.id if other_cat else None,
                'subcategory_id': None,
                'confidence': 0.0,
                'extracted_data': self._extract_data_simple(text)
            }
    
    def learn_from_correction(self, document_id: int, correct_category_id: int, 
                            correct_subcategory_id: Optional[int], text: str, user_id: int):
        """Learn from user corrections to improve model"""
        if not self.learning_enabled:
            return
        
        db = get_db()
        
        # Store learning record with user_id
        learning_record = LearningRecord(
            user_id=user_id,
            document_id=document_id,
            text_features=json.dumps({'text': text[:1000]}),
            category_id=correct_category_id,
            subcategory_id=correct_subcategory_id,
            confidence=1.0,
            was_correct=False
        )
        db.add(learning_record)
        db.commit()
        
        # Log the learning event
        record_count = db.query(LearningRecord).filter_by(user_id=user_id).count()
        print(f"AI Learning: Recorded correction for document {document_id} (user {user_id}), user records: {record_count}")
        
        # Retrain model if enough new data for this user
        if record_count % 10 == 0:
            print(f"AI Learning: Retraining model for user {user_id} with {record_count} records...")
            self._retrain_models()
        
        db.close()
    
    def _load_models(self):
        """Load trained ML models for specific user"""
        # Load category model
        model_filename = self._get_model_filename('category')
        cat_model_path = os.path.abspath(os.path.join(self.model_path, model_filename))
        print(f"AI: Attempting to load category model from: {cat_model_path}")
        print(f"AI: Model file exists: {os.path.exists(cat_model_path)}")
        
        if os.path.exists(cat_model_path):
            try:
                self.category_model = joblib.load(cat_model_path)
                print(f"AI: Category model loaded successfully for user {self.user_id}!")
            except Exception as e:
                print(f"Failed to load category model: {e}")
        else:
            print(f"AI: No category model file found at {cat_model_path}")
        
        # Load subcategory models for this user
        self.subcategory_models = {}
        
        # Pattern for user-specific models: user_{user_id}_subcategory_{cat_id}_model.pkl
        if self.user_id:
            prefix = f'user_{self.user_id}_subcategory_'
        else:
            prefix = 'subcategory_'
        
        model_files = [f for f in os.listdir(self.model_path) 
                      if f.startswith(prefix) and f.endswith('_model.pkl')]
        
        for model_file in model_files:
            try:
                # Extract category_id from filename
                parts = model_file.replace(prefix, '').replace('_model.pkl', '')
                category_id = int(parts)
                sub_model_path = os.path.abspath(os.path.join(self.model_path, model_file))
                self.subcategory_models[category_id] = joblib.load(sub_model_path)
                print(f"AI: Loaded subcategory model for category {category_id} (user {self.user_id})")
            except Exception as e:
                print(f"Failed to load subcategory model {model_file}: {e}")
        
        if self.subcategory_models:
            print(f"AI: Loaded {len(self.subcategory_models)} subcategory models for user {self.user_id}")
    
    def _retrain_models(self):
        """Retrain ML models with learning records for this user.
        If `self.user_id` is None, retrain models for all users that have learning records.
        """
        db = get_db()
        if not self.user_id:
            # Retrain for all users present in learning records
            user_rows = db.query(LearningRecord.user_id).distinct().all()
            user_ids = [r[0] for r in user_rows]
            if not user_ids:
                print("AI: No learning records found to retrain for any user")
                db.close()
                return
            print(f"AI: Retraining models for all users: {user_ids}")
            for uid in user_ids:
                try:
                    print(f"AI: Starting retraining for user {uid}")
                    AIProcessor(user_id=uid)._retrain_models()
                except Exception as e:
                    print(f"AI: Retraining for user {uid} failed: {e}")
            db.close()
            return
        
        # Only get learning records for this user
        records = db.query(LearningRecord).filter_by(user_id=self.user_id).all()
        
        print(f"AI: Starting retraining for user {self.user_id} with {len(records)} records")
        
        if len(records) < 3:
            print(f"AI: Need at least 3 records to train (currently have {len(records)})")
            db.close()
            return
        
        # Prepare training data for category model
        texts = []
        labels = []
        
        for record in records:
            features = json.loads(record.text_features)
            texts.append(features.get('text', ''))
            labels.append(record.category_id)
        
        print(f"AI: Training category model with {len(texts)} text samples")
        
        # Train category model
        self.category_model = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=1000)),
            ('clf', MultinomialNB())
        ])
        
        self.category_model.fit(texts, labels)
        print(f"AI: Category model training completed for user {self.user_id}")
        
        # Save category model with user-specific filename
        model_filename = self._get_model_filename('category')
        model_path = os.path.abspath(os.path.join(self.model_path, model_filename))
        print(f"AI: Saving category model to: {model_path}")
        
        try:
            joblib.dump(self.category_model, model_path)
            print(f"AI: Category model saved successfully")
            print(f"AI: Model file size: {os.path.getsize(model_path)} bytes")
        except Exception as e:
            print(f"AI: ERROR saving category model: {e}")
            import traceback
            traceback.print_exc()
        
        # Train subcategory models per category
        print(f"AI: Training subcategory models...")
        self.subcategory_models = {}
        
        # Group records by category
        from collections import defaultdict
        category_records = defaultdict(list)
        for record in records:
            if record.subcategory_id:  # Only records with subcategories
                category_records[record.category_id].append(record)
        
        # Train a model for each category that has subcategories
        for category_id, cat_records in category_records.items():
            if len(cat_records) >= 2:  # Need at least 2 examples
                sub_texts = []
                sub_labels = []
                for record in cat_records:
                    features = json.loads(record.text_features)
                    sub_texts.append(features.get('text', ''))
                    sub_labels.append(record.subcategory_id)
                
                # Check if we have multiple subcategories
                unique_subcats = set(sub_labels)
                if len(unique_subcats) > 1:
                    print(f"AI: Training subcategory model for category {category_id} with {len(sub_texts)} samples")
                    
                    sub_model = Pipeline([
                        ('tfidf', TfidfVectorizer(max_features=500)),
                        ('clf', MultinomialNB())
                    ])
                    
                    sub_model.fit(sub_texts, sub_labels)
                    self.subcategory_models[category_id] = sub_model
                    
                    # Save subcategory model with user-specific filename
                    model_filename = self._get_model_filename('subcategory', category_id)
                    sub_model_path = os.path.abspath(os.path.join(self.model_path, model_filename))
                    joblib.dump(sub_model, sub_model_path)
                    print(f"AI: Subcategory model for category {category_id} saved (user {self.user_id})")
        
        print(f"AI: Trained {len(self.subcategory_models)} subcategory models for user {self.user_id}")
        
        # Reload all models
        self._load_models()
        print(f"AI: All models reloaded successfully")
        
        db.close()
