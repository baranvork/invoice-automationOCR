import logging
import numpy as np
from typing import Dict, Any, List, Optional
import traceback
import easyocr
import cv2

class OCRProcessor:
    def __init__(self):
        # Logging ayarları
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler ekle
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '\n%(asctime)s - %(name)s - %(levelname)s\n%(message)s\n'
        )
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        
        self._reader = None

    @property
    def reader(self):
        """EasyOCR reader'ı lazy loading ile yükle"""
        if self._reader is None:
            try:
                self.logger.info("Initializing EasyOCR reader...")
                # Türkçe ve İngilizce desteği
                self._reader = easyocr.Reader(['tr', 'en'])
                self.logger.info("EasyOCR reader initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing EasyOCR reader: {str(e)}")
                raise
        return self._reader

    def process_document(self, image: np.ndarray) -> Dict[str, Any]:
        """Belgeyi işle"""
        self.logger.info("=== DOCUMENT PROCESSING STARTED ===")
        try:
            # OCR işlemi
            self.logger.info("\n=== OCR PROCESSING ===")
            ocr_results = self._perform_ocr(image)
            if not ocr_results:
                raise ValueError("OCR failed to extract text")
            
            self.logger.info(f"""
OCR Results:
------------
Text Length: {len(ocr_results['text'])}
Confidence: {ocr_results['confidence']:.2f}%
Number of Text Blocks: {len(ocr_results['blocks'])}
Sample Text: {ocr_results['text'][:200]}...
            """)
            
            results = {
                'success': True,
                'ocr': ocr_results,
                'confidence': ocr_results['confidence']
            }
            
            self.logger.info("\n=== PROCESSING COMPLETED ===")
            return results
            
        except Exception as e:
            self.logger.error(f"""
Processing Error:
---------------
Error Type: {type(e).__name__}
Error Message: {str(e)}
Stack Trace: {traceback.format_exc()}
            """)
            return {'success': False, 'error': str(e)}

    def _perform_ocr(self, image: np.ndarray) -> Optional[Dict[str, Any]]:
        """EasyOCR ile metin tanıma"""
        try:
            self.logger.info("Starting OCR text recognition...")
            
            # Görüntü boyutlarını kontrol et
            self.logger.info(f"Image shape: {image.shape}")
            
            # Görüntüyü BGR'den RGB'ye dönüştür
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # OCR işlemi
            self.logger.info("Running OCR recognition...")
            results = self.reader.readtext(image)
            
            if not results:
                raise ValueError("No text detected in image")
            
            text_blocks = []
            coordinates = []
            confidences = []
            
            self.logger.info("\nDetected Text Blocks:")
            self.logger.info("-" * 50)
            
            for idx, (bbox, text, conf) in enumerate(results):
                text_blocks.append(text)
                coordinates.append(bbox)
                confidences.append(conf)
                self.logger.info(f"Block {idx+1}: '{text}' (Confidence: {conf:.2f}%)")
            
            result = {
                'text': ' '.join(text_blocks),
                'blocks': text_blocks,
                'coordinates': coordinates,
                'confidence': np.mean(confidences) if confidences else 0
            }
            
            self.logger.info(f"""
OCR Summary:
-----------
Total Blocks: {len(text_blocks)}
Average Confidence: {result['confidence']:.2f}%
Total Text Length: {len(result['text'])}
            """)
            
            return result
            
        except Exception as e:
            self.logger.error(f"""
OCR Error:
---------
Error Type: {type(e).__name__}
Error Message: {str(e)}
Stack Trace: {traceback.format_exc()}
            """)
            return None 