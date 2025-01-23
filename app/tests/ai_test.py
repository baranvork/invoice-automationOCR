import os
import logging
import json
from typing import Dict, Any
from flask import Flask
from app.core.document_processor import DocumentProcessor  # Ana projedeki DocumentProcessor'ı kullan

# Flask uygulaması oluştur
app = Flask(__name__)

# Log dosyası için yolu belirle
current_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(current_dir, 'ai_test_results.log')

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='\n%(asctime)s - %(levelname)s\n%(message)s\n',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger(__name__)

def test_invoice():
    """Fatura işleme testi"""
    try:
        print("\n=== Starting Invoice Test ===\n")
        
        # Test görüntüsünü yükle
        image_path = os.path.join(current_dir, 'test-images', 'invoice.jpg')
        if not os.path.exists(image_path):
            print(f"\nTest image not found: {image_path}")
            return
            
        print(f"Processing image: {image_path}")
        
        # Document processor'ı başlat
        processor = DocumentProcessor()
        
        # Flask context'inde çalıştır
        with app.app_context():
            result = processor.process_document(image_path)
        
        if result and result.get('success'):
            print("\n=== OCR TEXT ===\n")
            print(result.get('text', ''))
            
            # Bölgesel sonuçları göster
            print("\n=== REGIONAL TEXT ===\n")
            for region, text in result.get('text_blocks', {}).items():
                print(f"\n{region.upper()}:")
                print(text)
            
            print("\n=== EXTRACTED DATA ===\n")
            invoice_data = result.get('invoice_data', {})
            print(json.dumps(invoice_data, indent=2, ensure_ascii=False))
            
            # Başarı kontrolü
            required_fields = ['vendor', 'date', 'total_amount']
            success_count = sum(1 for f in required_fields if invoice_data.get(f))
            print(f"\nSuccess Rate: {success_count}/{len(required_fields)}")
            
        else:
            print("Processing failed!")
            if result:
                print(f"Error: {result.get('error', 'Unknown error')}")
                
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_invoice()