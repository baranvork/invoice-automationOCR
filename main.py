# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import sys
sys.setrecursionlimit(10000)  # Recursion limitini artır

import os
import logging
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # TensorFlow loglarını kısıtla
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # oneDNN uyarılarını kapat

# Genel logging seviyesini ayarla
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('keras').setLevel(logging.ERROR)

from flask import Flask
from app.web import web_bp  # Web blueprint'i
from app.api import api_bp  # API blueprint'i
from app.core.document_processor import DocumentProcessor

def create_app(config_name='development'):
    app = Flask(__name__, 
                static_folder='app/static',  # Static dosyaların yolu
                template_folder='app/web/templates')  # Template'lerin yolu
    
    # Config yükleme
    if config_name == 'development':
        from config.development import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    else:
        from config.production import ProductionConfig
        app.config.from_object(ProductionConfig)
    
    # Performance optimizations
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
    app.config['TEMPLATES_AUTO_RELOAD'] = False
    
    # Upload klasörünü oluştur
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    app.logger.info(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    
    # Document processor'ı uygulama context'ine ekle
    app.document_processor = DocumentProcessor(app.config)
    
    # Blueprint'leri kaydet
    app.register_blueprint(web_bp)  # Web routes için
    app.register_blueprint(api_bp, url_prefix='/api')  # API routes için
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
# Press the green button in the gutter to run the script.
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
