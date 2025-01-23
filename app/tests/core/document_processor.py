import cv2
import logging
import os
import numpy as np
from typing import Dict, Any
from app.tests.core.ocr_processor import OCRProcessor
from flask import current_app

class DocumentProcessor:
    def __init__(self, config=None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.ocr_processor = OCRProcessor()

    def process_document(self, filepath):
        """Belgeyi işle"""
        try:
            # Görüntüyü yükle
            image = self._load_image(filepath)
            if image is None:
                current_app.logger.error(f"Failed to load image: {filepath}")
                return None

            # Görüntüyü ön işle
            processed_image = self._preprocess_image(image)

            # OCR işlemi
            result = self.ocr_processor.process_document(processed_image)
            
            return result

        except Exception as e:
            current_app.logger.error(f"Error processing document: {str(e)}")
            return None

    def _load_image(self, filepath):
        """Görüntüyü yükle"""
        try:
            image = cv2.imread(filepath)
            if image is None:
                raise ValueError("Failed to load image")
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