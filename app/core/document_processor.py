import cv2
import logging
import os
import tensorflow as tf
from .tf_processor import TensorFlowProcessor
from ..utils.file_helpers import save_analysis_results

class DocumentProcessor:
    def __init__(self, config=None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Sadece TensorFlow işlemcisini yükle
        self.tf_processor = TensorFlowProcessor()

    def process(self, file_path):
        # Görüntüyü yükle
        image = tf.io.read_file(file_path)
        image = tf.image.decode_image(image, channels=3)
        
        # TensorFlow işlemcisi ile OCR yap
        results = self.tf_processor.process_document(image)
        
        return {
            'text': results.get('ocr', {}).get('text', ''),
            'confidence': results.get('confidence', 0),
            'entities': results.get('entities', {}),
            'tables': results.get('tables', [])
        }

    def process_document(self, image_path):
        try:
            # 1. Görüntüyü oku
            self.logger.info(f"Reading image from: {image_path}")
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Could not read image file")
            
            # BGR'den RGB'ye dönüştür
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 2. Görüntü ön işleme
            self.logger.info("Preprocessing image...")
            preprocessed_image = self._preprocess_image(image)
            
            # 3. TensorFlow işleme
            self.logger.info("Processing with TensorFlow...")
            tf_results = self.tf_processor.process_document(preprocessed_image)
            
            if not tf_results.get('success'):
                raise ValueError(tf_results.get('error', 'Unknown processing error'))
            
            return self._format_results(tf_results)

        except Exception as e:
            self.logger.error(f"Error processing document: {str(e)}")
            return None

    def _preprocess_image(self, image):
        """Görüntü ön işleme"""
        # Boyut kontrolü
        max_dimension = 1800
        height, width = image.shape[:2]
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            image = cv2.resize(image, None, fx=scale, fy=scale)
        
        return image

    def _format_results(self, tf_results):
        """TensorFlow sonuçlarını API formatına dönüştür"""
        return {
            'success': tf_results['success'],
            'confidence': tf_results['confidence'],
            'entities': {
                'companies': {
                    'sender': tf_results['entities'].get('ORG_SENDER'),
                    'recipient': tf_results['entities'].get('ORG_RECIPIENT')
                },
                'addresses': {
                    'sender': tf_results['entities'].get('ADDR_SENDER'),
                    'recipient': tf_results['entities'].get('ADDR_RECIPIENT')
                },
                'amounts': {
                    'subtotal': tf_results['entities'].get('AMOUNT_SUBTOTAL'),
                    'tax': tf_results['entities'].get('AMOUNT_TAX'),
                    'total': tf_results['entities'].get('AMOUNT_TOTAL')
                },
                'dates': {
                    'invoice_date': tf_results['entities'].get('DATE_INVOICE'),
                    'due_date': tf_results['entities'].get('DATE_DUE')
                }
            },
            'ocr_details': {
                'text': tf_results['ocr']['text'],
                'confidence': tf_results['ocr']['confidence']
            },
            'tables': tf_results['tables']
        } 