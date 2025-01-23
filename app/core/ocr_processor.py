import logging
import numpy as np
from typing import Dict, Any, Tuple, List
import traceback
import pytesseract
import cv2
from datetime import datetime
import re
from flask import current_app

class OCRProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Anahtar kelime ve başlıklar
        self.field_headers = {
            'vendor': ['vendor:', 'seller:', 'company:', 'business name:', 'supplier:'],
            'date': ['date:', 'invoice date:', 'bill date:', 'issued date:'],
            'total': ['total:', 'total amount:', 'grand total:', 'amount due:', 'balance due:'],
            'tax': ['tax:', 'vat:', 'tax amount:', 'kdv:'],
            'invoice_no': ['invoice no:', 'invoice number:', 'bill no:', 'reference:']
        }

    def process_document(self, image: np.ndarray) -> Dict[str, Any]:
        """Belgeyi işle"""
        try:
            if self.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

            # Görüntü ön işleme
            processed_image = self._preprocess_image(image)
            
            # Bölgesel OCR uygula
            regions = self._extract_regions(processed_image)
            text_blocks = {}
            
            for region_name, region_img in regions.items():
                # Her bölge için OCR
                text = pytesseract.image_to_string(region_img, lang='eng+tur')
                text_blocks[region_name] = text

            # Tüm metni birleştir
            full_text = '\n'.join(text_blocks.values())
            
            # Fatura verilerini çıkar
            invoice_data = self._extract_invoice_data(full_text, text_blocks)
            
            return {
                'success': True,
                'text': full_text,
                'text_blocks': text_blocks,
                'confidence': 0,
                'invoice_data': invoice_data
            }
            
        except Exception as e:
            self.logger.error(f"OCR Error: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Görüntü ön işleme"""
        try:
            # Gri tonlamaya çevir
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Gürültü azaltma
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Kontrast artırma
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Eğrilik düzeltme
            coords = np.column_stack(np.where(enhanced > 0))
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = 90 + angle
            center = (image.shape[1] // 2, image.shape[0] // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(enhanced, M, (image.shape[1], image.shape[0]),
                                   flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            
            # Adaptif eşikleme
            thresh = cv2.adaptiveThreshold(rotated, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY, 11, 2)
            
            return thresh
            
        except Exception as e:
            self.logger.error(f"Error in preprocessing: {str(e)}")
            return image

    def _extract_regions(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """Görüntüyü bölgelere ayır"""
        height, width = image.shape[:2]
        
        regions = {
            'header': image[0:int(height*0.3), :],              # Üst %30
            'body': image[int(height*0.3):int(height*0.7), :],  # Orta %40
            'footer': image[int(height*0.7):, :]               # Alt %30
        }
        
        return regions

    def _extract_invoice_data(self, text: str, text_blocks: Dict[str, str]) -> Dict[str, Any]:
        """Metin içinden fatura verilerini çıkar"""
        lines = text.split('\n')
        data = {
            'vendor': '',
            'date': '',
            'total_amount': 0.0,
            'tax_amount': 0.0,
            'invoice_number': '',
            'tax_id': '',
            'category': 'others',
            'address': '',
            'currency': ''
        }

        # Başlık tabanlı arama
        for field, headers in self.field_headers.items():
            value = self._find_value_after_header(text, headers)
            if value:
                if field == 'total':
                    data['total_amount'] = self._extract_amount(value)
                elif field == 'tax':
                    data['tax_amount'] = self._extract_amount(value)
                else:
                    data[field] = value.strip()

        # Header bölgesinden vendor ve invoice number
        header_text = text_blocks.get('header', '')
        if not data['vendor']:
            for line in header_text.split('\n')[:5]:
                if line and not any(keyword in line.lower() for keyword in 
                    ['invoice', 'date', 'tel', 'fax', 'no.']):
                    data['vendor'] = line.strip()
                    break

        # Tarih bul
        if not data['date']:
            date_pattern = r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b'
            for line in lines:
                if date_match := re.search(date_pattern, line):
                    date_str = date_match.group()
                    try:
                        if '-' in date_str:
                            date = datetime.strptime(date_str, '%d-%m-%Y')
                        else:
                            date = datetime.strptime(date_str, '%d/%m/%Y')
                        data['date'] = date.strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        continue

        # Adres bul (NO ve / içeren satırlar)
        address_pattern = r'.*NO.*/.+'
        for line in lines:
            if re.match(address_pattern, line, re.IGNORECASE):
                data['address'] = line.strip()
                break

        # Para birimi ve tutarı bul
        if not data['total_amount']:
            amount_patterns = [
                (r'(\d+(?:[.,]\d{2})?)\s*TR', 'TRY'),
                (r'(\d+(?:[.,]\d{2})?)\s*USD', 'USD'),
                (r'(\d+(?:[.,]\d{2})?)\s*EUR', 'EUR')
            ]
            
            for line in lines:
                for pattern, currency in amount_patterns:
                    if amount_match := re.search(pattern, line):
                        try:
                            amount = float(amount_match.group(1).replace(',', '.'))
                            data['total_amount'] = amount
                            data['currency'] = currency
                            break
                        except ValueError:
                            continue
                if data['total_amount'] > 0:
                    break

        return data

    def _find_value_after_header(self, text: str, headers: List[str]) -> str:
        """Başlıktan sonraki değeri bul"""
        lines = text.lower().split('\n')
        for i, line in enumerate(lines):
            for header in headers:
                if header in line:
                    # Değer aynı satırda olabilir
                    value = line.split(header)[-1].strip()
                    if value:
                        return value
                    # Değer sonraki satırda olabilir
                    if i + 1 < len(lines):
                        return lines[i + 1].strip()
        return ''

    def _extract_amount(self, text: str) -> float:
        """Metin içinden sayısal değeri çıkar"""
        try:
            amount = re.search(r'(\d+(?:[.,]\d{2})?)', text)
            if amount:
                return float(amount.group(1).replace(',', '.'))
        except:
            pass
        return 0.0 