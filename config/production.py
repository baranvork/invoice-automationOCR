class ProductionConfig:
    DEBUG = False
    UPLOAD_FOLDER = '/var/www/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    
    # OCR ayarları
    OCR_ENGINE = 'tesseract'
    TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    # API ayarları
    API_PREFIX = '/api/v1' 