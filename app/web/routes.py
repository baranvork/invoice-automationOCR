from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from app.core.document_processor import DocumentProcessor
from app.utils.file_helpers import allowed_file

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    return render_template('index.html')

@web_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})
        
    if file and allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Document processor ile işle
            document_processor = DocumentProcessor(current_app.config)
            result = document_processor.process_document(filepath)
            
            if not result:
                return jsonify({
                    'success': False,
                    'error': 'Document processing failed'
                })
            
            return jsonify({
                'success': True,
                'text': result.get('ocr_details', {}).get('text', ''),
                'entities': result.get('entities', {}),
                'confidence': result.get('confidence', 0)
            })
            
        except Exception as e:
            current_app.logger.error(f"Error processing upload: {str(e)}")
            return jsonify({'success': False, 'error': str(e)})
            
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
    
    return jsonify({'success': False, 'error': 'Invalid file type'}) 