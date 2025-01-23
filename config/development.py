class DevelopmentConfig:
    DEBUG = True
    OCR_ENGINE = 'tesseract'
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'tiff'}
    
    # OCR ayarları
    TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows için Tesseract yolu
    
    # API ayarları
    API_PREFIX = '/api/v1' 
    
    # Performans ayarları
    OCR_MAX_DIMENSION = 1800
    OCR_THREAD_COUNT = 2
    NER_THREAD_COUNT = 3
    BATCH_SIZE = 16
    USE_CUDA = False  # GPU varsa True yapın
    
    # Cache ayarları
    CACHE_DIR = 'cache'
    MAX_CACHE_SIZE = 1000 