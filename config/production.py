class ProductionConfig:
    DEBUG = False
    SECRET_KEY = 'your-production-secret-key'  # Güvenli bir key kullanın
    UPLOAD_FOLDER = '/var/www/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # SQLAlchemy ayarları
    SQLALCHEMY_DATABASE_URI = 'sqlite:///invoices.db'  # Production'da farklı bir DB kullanabilirsiniz
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OCR ayarları
    OCR_MAX_DIMENSION = 1800
    OCR_LANGUAGES = ['tr', 'en']
    
    # OCR ayarları
    OCR_ENGINE = 'tesseract'
    TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    # API ayarları
    API_PREFIX = '/api/v1' 