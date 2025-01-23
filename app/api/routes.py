from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from app.core.ocr_processor import OCRProcessor
from app.core.ner.model import NERModel

api_bp = Blueprint('api', __name__)
ocr_engine = None
ner_model = None

@api_bp.before_app_request
def initialize():
    global ocr_engine, ner_model
    if ocr_engine is None:
        ocr_engine = OCRProcessor()
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
            result = ocr_engine.process_document(filepath)
            
            if not result.get('success'):
                return jsonify({
                    'success': False,
                    'error': 'OCR processing failed'
                }), 500

            # NER işlemi
            entities = ner_model.extract_entities(result['ocr']['text'])
            
            return jsonify({
                'success': True,
                'text': result['ocr']['text'],
                'confidence': result['ocr']['confidence'],
                'entities': entities,
                'blocks': result['ocr']['blocks']
            })
            
        except Exception as e:
            current_app.logger.error(f"Error processing upload: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
        finally:
            # Dosyayı sil
            if os.path.exists(filepath):
                os.remove(filepath)
    
    return jsonify({'error': 'Invalid file type'}), 400 