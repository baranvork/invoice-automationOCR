import cv2
import pytesseract
from PIL import Image
import numpy as np
from pdf2image import convert_from_path
from app.utils.helpers import preprocess_image
from concurrent.futures import ThreadPoolExecutor

class OCREngine:
    def __init__(self, config):
        self.config = config or {}
        # Config'den tesseract yolunu al
        pytesseract.pytesseract.tesseract_cmd = self.config.get('TESSERACT_CMD', r'C:\Program Files\Tesseract-OCR\tesseract.exe')

    def process_image(self, image_path):
        """
        Extract text from image with optimizations
        """
        try:
            # Görüntüyü küçült
            image = cv2.imread(image_path)
            height, width = image.shape[:2]
            
            # Maksimum boyut 1800px
            max_dimension = 1800
            if max(height, width) > max_dimension:
                scale = max_dimension / max(height, width)
                image = cv2.resize(image, None, fx=scale, fy=scale)

            # Thread pool kullan
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Paralel işlemler
                future_preprocess = executor.submit(preprocess_image, image)
                future_grayscale = executor.submit(cv2.cvtColor, image, cv2.COLOR_BGR2GRAY)
                
                processed_image = future_preprocess.result()
                gray_image = future_grayscale.result()

            # OCR yapılandırması - hızlı mod
            custom_config = r'--oem 3 --psm 6 -l eng --dpi 300'
            
            # OCR işlemi
            text = pytesseract.image_to_string(
                processed_image,
                config=custom_config,
                nice=0  # CPU önceliği
            )
            
            return {'text': text, 'conf': 100}  # Basitleştirilmiş çıktı

        except Exception as e:
            self.logger.error(f"Error in OCR: {str(e)}")
            return None

    def _get_confidence(self, image):
        """
        OCR güven skorunu hesapla
        """
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        confidences = [int(conf) for conf in data['conf'] if conf != '-1']
        return sum(confidences) / len(confidences) if confidences else 0 