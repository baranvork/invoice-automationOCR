import cv2
import logging
import os
import numpy as np
from .ocr_processor import OCRProcessor
from ..utils.file_helpers import save_analysis_results
from flask import current_app
from .ner.model import NERModel  # NERProcessor yerine NERModel'i import et

class DocumentProcessor:
    def __init__(self, config=None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # OCR ve NER işlemcilerini yükle
        self.ocr_processor = OCRProcessor()
        self.ner_processor = NERModel()  # NERProcessor yerine NERModel kullan

    def process_document(self, filepath):
        """Belgeyi işle"""
        try:
            # Görüntüyü yükle
            image = self._load_image(filepath)
            if image is None:
                current_app.logger.error(f"Failed to load image: {filepath}")
                return None

            # OCR işlemi
            ocr_result = self.ocr_processor.process_document(image)
            
            # Debug için OCR sonuçlarını logla
            current_app.logger.info(f"OCR Result for {filepath}: {ocr_result}")
            
            if not ocr_result:
                current_app.logger.error(f"OCR processing failed for {filepath}")
                return None

            # OCR sonuçlarını kontrol et
            if not ocr_result.get('text'):
                current_app.logger.warning(f"No text extracted from {filepath}")

            # NER işlemi
            text = ocr_result.get('text', '')
            ner_result = self.ner_processor.process_text(text)

            # Sonuçları birleştir
            return {
                'success': True,
                'text': text,
                'confidence': ocr_result.get('confidence', 0),
                'invoice_data': ner_result if ner_result else {}
            }
        except Exception as e:
            current_app.logger.error(f"Error processing document: {str(e)}")
            return None

    def _load_image(self, filepath):
        """Görüntüyü yükle ve ön işle"""
        try:
            # Görüntüyü oku
            image = cv2.imread(filepath)
            if image is None:
                raise ValueError("Failed to load image")

            # Görüntü boyutunu kontrol et
            max_dimension = self.config.get('OCR_MAX_DIMENSION', 1800)
            height, width = image.shape[:2]
            
            # Boyut çok büyükse yeniden boyutlandır
            if height > max_dimension or width > max_dimension:
                scale = max_dimension / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height))

            return image

        except Exception as e:
            self.logger.error(f"Error loading image: {str(e)}")
            return None

    def _preprocess_image(self, image):
        """Görüntü ön işleme"""
        try:
            # Gri tonlamaya çevir
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Gürültü azaltma
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Adaptif eşikleme
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Keskinleştirme
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(thresh, -1, kernel)
            
            return sharpened
        except Exception as e:
            self.logger.error(f"Error in preprocessing: {str(e)}")
            return image

    def _format_results(self, results):
        """Sonuçları formatla"""
        try:
            # Debug için
            self.logger.info(f"Formatting results: {results}")
            
            return {
                'success': True,
                'text': results.get('ocr', {}).get('text', ''),
                'confidence': results.get('ocr', {}).get('confidence', 0),
                'blocks': results.get('ocr', {}).get('blocks', [])
            }
        except Exception as e:
            self.logger.error(f"Error formatting results: {str(e)}")
            return None 