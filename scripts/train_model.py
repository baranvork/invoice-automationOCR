import tensorflow as tf
import numpy as np
import os
import json
from app.core.document_processor import DocumentProcessor

def prepare_training_data(data_dir):
    """Eğitim verilerini hazırla"""
    X = []  # Özellikler
    y = []  # Etiketler
    
    # Etiketli veri setini yükle
    with open(os.path.join(data_dir, 'labels.json'), 'r') as f:
        labels = json.load(f)
    
    processor = DocumentProcessor()
    
    # Her fatura için özellikleri çıkar
    for image_file, label_data in labels.items():
        image_path = os.path.join(data_dir, 'images', image_file)
        
        # Özellikleri çıkar
        text_result = processor.text_extractor.extract_text_from_image(image_path)
        ocr_result = processor.ocr_engine.process_image(image_path)
        
        # Özellikleri hazırla
        features = processor._prepare_features(text_result, ocr_result)
        X.append(features)
        
        # Etiketleri hazırla
        y.append({
            'company': 1 if label_data['companies']['sender'] else 0,
            'amount': [
                1 if label_data['amounts']['subtotal'] else 0,
                1 if label_data['amounts']['taxes'] else 0,
                1 if label_data['amounts']['total'] else 0
            ],
            'date': [
                1 if label_data['dates']['invoice_date'] else 0,
                1 if label_data['dates']['due_date'] else 0
            ],
            'address': 1 if label_data['addresses']['sender'] else 0
        })
    
    return np.array(X), y

def train_model():
    """Modeli eğit"""
    # Veri setini hazırla
    X_train, y_train = prepare_training_data('data/training')
    
    # Modeli oluştur
    processor = DocumentProcessor()
    model = processor._create_basic_model()
    
    # Modeli eğit
    model.fit(
        X_train,
        y_train,
        epochs=50,
        batch_size=32,
        validation_split=0.2
    )
    
    # Modeli kaydet
    model.save('app/models/invoice_model')

if __name__ == '__main__':
    train_model() 