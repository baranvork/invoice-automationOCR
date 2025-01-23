import os

class DevelopmentConfig:
    DEBUG = True
    SECRET_KEY = 'dev-secret-key'
    UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # SQLAlchemy ayarları
    SQLALCHEMY_DATABASE_URI = 'sqlite:///invoices.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OCR ayarları
    OCR_MAX_DIMENSION = 1800
    OCR_LANGUAGES = ['tr', 'en']
    
    # OCR ayarları
    OCR_ENGINE = 'tesseract'
    OCR_THREAD_COUNT = 2
    NER_THREAD_COUNT = 3
    BATCH_SIZE = 16
    USE_CUDA = False  # GPU varsa True yapın
    
    # Cache ayarları
    CACHE_DIR = 'cache'
    MAX_CACHE_SIZE = 1000
    
    # API ayarları
    API_PREFIX = '/api/v1'
    
    # Tesseract yolu
    TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows için Tesseract yolu 