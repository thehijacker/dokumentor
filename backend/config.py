import os
import yaml
from typing import Any, Dict, List


class Config:
    """Configuration manager that handles config.yaml and environment variables"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load_config()
        self.apply_env_overrides()
    
    def load_config(self):
        """Load configuration from YAML file"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        else:
            print(f"Warning: Config file {self.config_path} not found, using defaults")
            self.config = self._get_defaults()
    
    def apply_env_overrides(self):
        """Override config values with environment variables"""
        # Application
        if secret_key := os.getenv('APP_SECRET_KEY'):
            self.config.setdefault('app', {})['secret_key'] = secret_key
        if debug := os.getenv('APP_DEBUG'):
            self.config.setdefault('app', {})['debug'] = debug.lower() == 'true'
        
        # Database
        if db_path := os.getenv('DATABASE_PATH'):
            self.config.setdefault('database', {})['path'] = db_path
        
        # Storage
        if docs_path := os.getenv('DOCUMENTS_PATH'):
            self.config.setdefault('storage', {})['documents_path'] = docs_path
        if watch_folder := os.getenv('WATCH_FOLDER'):
            self.config.setdefault('storage', {})['watch_folder'] = watch_folder
        
        # Authentication
        if enable_reg := os.getenv('ENABLE_REGISTRATION'):
            self.config.setdefault('auth', {})['enable_registration'] = enable_reg.lower() == 'true'
        
        # OCR
        if ocr_langs := os.getenv('OCR_DEFAULT_LANGUAGES'):
            self.config.setdefault('ocr', {})['default_languages'] = ocr_langs.split(',')
        if tesseract_path := os.getenv('TESSERACT_PATH'):
            self.config.setdefault('ocr', {})['tesseract_path'] = tesseract_path
        if ocr_engine := os.getenv('OCR_ENGINE'):
            self.config.setdefault('ocr', {})['engine'] = ocr_engine
        
        # PDF
        if pdf_passwords := os.getenv('PDF_DECRYPT_PASSWORDS'):
            self.config.setdefault('pdf', {})['decrypt_passwords'] = pdf_passwords.split(',')
        
        # AI
        if ai_provider := os.getenv('AI_PROVIDER'):
            self.config.setdefault('ai', {})['provider'] = ai_provider
        if ai_model := os.getenv('AI_MODEL'):
            self.config.setdefault('ai', {})['model'] = ai_model
        if openai_key := os.getenv('OPENAI_API_KEY'):
            self.config.setdefault('ai', {})['openai_api_key'] = openai_key
        if ollama_url := os.getenv('OLLAMA_URL'):
            self.config.setdefault('ai', {})['ollama_url'] = ollama_url
        if ollama_model := os.getenv('OLLAMA_MODEL'):
            self.config.setdefault('ai', {})['ollama_model'] = ollama_model
        
        # Watch Folder
        if watch_enabled := os.getenv('WATCH_FOLDER_ENABLED'):
            self.config.setdefault('watch_folder', {})['enabled'] = watch_enabled.lower() == 'true'

        # Cookie security (controls SESSION_COOKIE_SECURE / REMEMBER_COOKIE_SECURE)
        if secure := os.getenv('APP_SECURE_COOKIES'):
            self.config.setdefault('app', {})['secure_cookies'] = secure.lower() == 'true' 
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            'app': {
                'name': 'Dokumentor',
                'secret_key': 'change-this-secret-key',
                'debug': False,
                'secure_cookies': True
            },
            'server': {
                'host': '0.0.0.0',
                'port': 5000
            },
            'database': {
                'path': './data/documents.db'
            },
            'storage': {
                'documents_path': './documents',
                'watch_folder': './watch_folder'
            },
            'auth': {
                'enable_registration': True
            },
            'ocr': {
                'enabled': True,
                'default_languages': ['eng', 'slv']
            },
            'ai': {
                'provider': 'internal',
                'model': 'simple'
            },
            'watch_folder': {
                'enabled': True,
                'interval': 10
            }
        }


# Global config instance
config = Config()
