import cv2
import logging
import os
import numpy as np
from .ocr_processor import OCRProcessor
from ..utils.file_helpers import save_analysis_results

class DocumentProcessor:
    def __init__(self, config=None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Sadece TensorFlow işlemcisini yükle
        self.ocr_processor = OCRProcessor()

    def process(self, file_path):
        # Görüntüyü yükle
        image = tf.io.read_file(file_path)
        image = tf.image.decode_image(image, channels=3)
        
        # TensorFlow işlemcisi ile OCR yap
        results = self.ocr_processor.process_document(image)
        
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
            
            # 2. Görüntü ön işleme
            self.logger.info("Preprocessing image...")
            preprocessed_image = self._preprocess_image(image)
            
            # 3. OCR işleme
            self.logger.info("Processing with OCR...")
            results = self.ocr_processor.process_document(preprocessed_image)
            
            if not results.get('success'):
                raise ValueError(results.get('error', 'Unknown processing error'))
            
            return self._format_results(results)

        except Exception as e:
            self.logger.error(f"Error processing document: {str(e)}")
            return None

    def _preprocess_image(self, image):
        """Görüntü ön işleme"""
        try:
            # Boyut kontrolü
            max_dimension = 1800
            height, width = image.shape[:2]
            if max(height, width) > max_dimension:
                scale = max_dimension / max(height, width)
                image = cv2.resize(image, None, fx=scale, fy=scale)
            
            # Gürültü azaltma
            denoised = cv2.fastNlMeansDenoisingColored(image)
            
            # Keskinleştirme
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(denoised, -1, kernel)
            
            return sharpened
            
        except Exception as e:
            self.logger.error(f"Error in preprocessing: {str(e)}")
            return image

    def _format_results(self, results):
        """Sonuçları formatla"""
        return {
            'success': True,
            'text': results['ocr']['text'],
            'confidence': results['ocr']['confidence'],
            'blocks': results['ocr']['blocks']
        } 