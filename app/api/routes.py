from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from app.core.ocr_engine import OCREngine
from app.core.ner.model import NERModel

api_bp = Blueprint('api', __name__)
ocr_engine = None
ner_model = None

@api_bp.before_app_request
def initialize():
    global ocr_engine, ner_model
    if ocr_engine is None:
        ocr_engine = OCREngine(current_app.config)
    if ner_model is None:
        ner_model = NERModel()

@api_bp.route('/process', methods=['POST'])
def process_invoice():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # OCR işlemi
            text = ocr_engine.process_image(filepath)
            
            # NER işlemi
            entities = ner_model.extract_entities(text['text'])
            
            return jsonify({
                'success': True,
                'text': text['text'],
                'entities': {
                    'companies': entities['companies'],
                    'amounts': entities['amounts'],
                    'dates': entities['dates'],
                    'addresses': entities['addresses']
                }
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Dosyayı sil
            if os.path.exists(filepath):
                os.remove(filepath) 