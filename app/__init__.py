# Bu dosya boş olabilir, sadece klasörün bir Python paketi olduğunu belirtir 

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config

# SQLAlchemy instance'ı oluştur
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Config yükle
    app.config.from_object(config[config_name])
    
    # Veritabanını başlat
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Uploads klasörünü oluştur
    import os
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    
    # Blueprint'leri kaydet
    from .web.routes import web_bp
    app.register_blueprint(web_bp)
    
    # Veritabanı tablolarını oluştur
    with app.app_context():
        db.create_all()
    
    return app 