# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import os
import sys
sys.setrecursionlimit(10000)  # Recursion limitini artır

import logging
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # TensorFlow loglarını kısıtla
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # oneDNN uyarılarını kapat

# Genel logging seviyesini ayarla
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('keras').setLevel(logging.ERROR)

from flask import Flask
from flask_cors import CORS
from app import create_app

# Uygulama oluştur
app = create_app('development')

# CORS ayarları
CORS(app)

# Klasör yapılandırmaları
base_dir = os.path.dirname(os.path.abspath(__file__))
app.template_folder = os.path.join(base_dir, 'app', 'web', 'templates')
app.static_folder = os.path.join(base_dir, 'app', 'static')

# Uploads klasörünü oluştur
uploads_dir = os.path.join(base_dir, 'uploads')
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
app.config['UPLOAD_FOLDER'] = uploads_dir

if __name__ == '__main__':
    app.run(debug=True, port=5000)
# Press the green button in the gutter to run the script.
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
