import logging
import os
import pytesseract
from PIL import Image
import cv2
from app.utils.helpers import preprocess_image

class TextExtractor:
    def __init__(self, config=None):
        self.config = config or {}
        # Tesseract yolunu config'den al veya varsayılan değeri kullan
        pytesseract.pytesseract.tesseract_cmd = self.config.get(
            'TESSERACT_CMD', 
            r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        )
        self.confidence_threshold = self.config.get('CONFIDENCE_THRESHOLD', 60)
        
        # Logging ayarları
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def extract_text_from_image(self, image_path):
        """
        Görüntüden metin çıkarma işlemi
        """
        try:
            # Dosya kontrolü
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"The file {image_path} does not exist")

            print("\n=== OCR İŞLEMİ BAŞLADI ===")
            print(f"İşlenen dosya: {image_path}")

            # Görüntüyü oku
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Could not read image")

            # Görüntü ön işleme
            processed_image = preprocess_image(image)
            print("\nGörüntü ön işleme tamamlandı")
            
            # Görüntüyü büyüt
            processed_image = cv2.resize(processed_image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            print("Görüntü büyütme tamamlandı")
            
            # OCR yapılandırması
            custom_config = r'--oem 3 --psm 6 -l eng'
            
            # OCR işlemi
            print("\nOCR işlemi başlıyor...")
            ocr_data = pytesseract.image_to_data(
                processed_image,
                output_type=pytesseract.Output.DICT,
                config=custom_config
            )

            print("\n=== HAM OCR SONUÇLARI ===")
            # Her kelime ve güven skorunu yazdır
            for i, (word, conf) in enumerate(zip(ocr_data['text'], ocr_data['conf'])):
                if word.strip():  # Boş olmayan kelimeler
                    print(f"Kelime {i+1}: '{word}' (Güven: {conf}%)")

            # Güven skoruna göre filtreleme
            print("\n=== FİLTRELENMİŞ SATIRLAR ===")
            extracted_lines = []
            current_line = []
            last_line_num = -1

            for i, word in enumerate(ocr_data['text']):
                confidence = int(ocr_data['conf'][i])
                if confidence > self.confidence_threshold and word.strip():
                    line_num = ocr_data['line_num'][i]
                    if line_num != last_line_num:
                        if current_line:
                            line_text = ' '.join(current_line).strip()
                            if line_text:
                                extracted_lines.append(line_text)
                                print(f"Satır {len(extracted_lines)}: {line_text}")
                        current_line = [word]
                        last_line_num = line_num
                    else:
                        current_line.append(word)

            # Son satırı ekle
            if current_line:
                line_text = ' '.join(current_line).strip()
                if line_text:
                    extracted_lines.append(line_text)
                    print(f"Satır {len(extracted_lines)}: {line_text}")

            # Metni birleştir
            extracted_text = '\n'.join(extracted_lines)
            
            print("\n=== SONUÇ İSTATİSTİKLERİ ===")
            print(f"Toplam kelime sayısı: {len([w for w in ocr_data['text'] if w.strip()])}")
            print(f"Toplam satır sayısı: {len(extracted_lines)}")
            print(f"Ortalama güven skoru: {self._calculate_average_confidence(ocr_data):.2f}%")
            
            # Metin kalitesi kontrolü
            if not extracted_text.strip():
                print("\nUYARI: Metinden hiç içerik çıkarılamadı!")
                self.logger.warning("No text was extracted from the image")
                return None

            print("\n=== SON ÇIKTI ===")
            print(extracted_text)
            print("\n=== OCR İŞLEMİ TAMAMLANDI ===")

            return {
                'text': extracted_text,
                'confidence': self._calculate_average_confidence(ocr_data),
                'word_count': len([w for w in ocr_data['text'] if w.strip()]),
                'line_count': len(extracted_lines)
            }

        except Exception as e:
            print(f"\nHATA: {str(e)}")
            self.logger.error(f"Error extracting text: {str(e)}")
            raise

    def _calculate_average_confidence(self, ocr_data):
        """
        OCR güven skorlarının ortalamasını hesapla
        """
        confidences = [conf for conf in ocr_data['conf'] if conf != -1]
        return sum(confidences) / len(confidences) if confidences else 0

    def enhance_text_quality(self, text):
        """
        Çıkarılan metni iyileştir
        """
        if not text:
            return text

        # Gereksiz boşlukları temizle
        text = ' '.join(text.split())
        
        # Satır sonlarını düzelt
        text = text.replace('\n\n', '\n').strip()
        
        # Özel karakterleri düzelt
        text = text.replace('|', 'I')  # Yaygın OCR hatası
        text = text.replace('0', 'O')  # Sayı/harf karışıklığı
        
        return text

    def validate_extraction(self, result):
        """
        Çıkarma işleminin kalitesini kontrol et
        """
        if not result or not result['text']:
            return False
            
        # Minimum güven skoru kontrolü
        if result['confidence'] < self.confidence_threshold:
            return False
            
        # Minimum kelime sayısı kontrolü
        if result['word_count'] < 10:  # Örnek eşik değeri
            return False
            
        return True 