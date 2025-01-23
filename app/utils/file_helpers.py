import os
import json
from datetime import datetime

def allowed_file(filename, allowed_extensions):
    """Dosya uzantısının izin verilen uzantılardan olup olmadığını kontrol et"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions 

def save_analysis_results(results, base_folder='uploads/analysis'):
    """Analiz sonuçlarını JSON dosyası olarak kaydet"""
    
    # Klasör yapısını oluştur
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    analysis_folder = os.path.join(base_folder, timestamp)
    os.makedirs(analysis_folder, exist_ok=True)
    
    # TensorFlow sonuçlarını kaydet
    tf_path = os.path.join(analysis_folder, 'tensorflow_results.json')
    with open(tf_path, 'w', encoding='utf-8') as f:
        json.dump(results['tensorflow'], f, indent=2, ensure_ascii=False)
    
    # OCR sonuçlarını kaydet
    ocr_path = os.path.join(analysis_folder, 'ocr_results.json')
    with open(ocr_path, 'w', encoding='utf-8') as f:
        json.dump(results['ocr_details'], f, indent=2, ensure_ascii=False)
    
    # Birleştirilmiş sonuçları kaydet
    final_path = os.path.join(analysis_folder, 'final_results.json')
    with open(final_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    return analysis_folder 