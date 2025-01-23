import re
import logging
from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal

@dataclass
class ProductItem:
    """Ürün detaylarını tutan sınıf"""
    code: Optional[str] = None        # Ürün kodu
    description: Optional[str] = None # Ürün açıklaması
    quantity: Optional[float] = None  # Miktar
    unit_price: Optional[Decimal] = None  # Birim fiyat
    total: Optional[Decimal] = None   # Toplam tutar
    unit: Optional[str] = None        # Birim (adet, kg, lt vb.)

class ProductExtractor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Ürün satırı kalıpları - faturaya özel
        self.product_patterns = [
            # Kod + Miktar + Fiyat formatı
            r'(\d+)\s+(\d+)\s+(\d+\.\d{2})',
            # SR: ile başlayan açıklama satırları
            r'SR[:\.]?\s*(.*?)(?=\d|\n|$)',
        ]
        
        # Birim kalıpları
        self.unit_patterns = {
            'piece': r'(?:PC|PCS|PIECE|ADET)',
            'meter': r'(?:M|MTR|METER)',
            'kilogram': r'(?:KG|KILO|KILOGRAM)',
            'liter': r'(?:L|LT|LITER)',
            'set': r'(?:SET|TAKIM)',
        }

    def extract_products(self, text: str) -> List[ProductItem]:
        """Metinden ürün detaylarını çıkar"""
        products = []
        lines = text.split('\n')
        
        current_product = None
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Kod + Miktar + Fiyat satırı
            if match := re.match(r'(\d+)\s+(\d+)\s+(\d+\.\d{2})', line):
                if current_product:
                    products.append(current_product)
                    
                current_product = ProductItem(
                    code=match.group(1),
                    quantity=float(match.group(2)),
                    unit_price=Decimal(match.group(3))
                )
                current_product.total = Decimal(str(current_product.quantity)) * current_product.unit_price
                
            # Açıklama satırı
            elif 'SR' in line.upper() and current_product:
                desc_match = re.search(r'SR[:\.]?\s*(.*?)(?=\d|\n|$)', line, re.IGNORECASE)
                if desc_match:
                    current_product.description = desc_match.group(1).strip()
        
        # Son ürünü ekle
        if current_product:
            products.append(current_product)
        
        return products

    def _clean_description(self, text: str) -> str:
        """Açıklama metnini temizle"""
        # Gereksiz karakterleri kaldır
        text = re.sub(r'["\']', '', text)
        # Çoklu boşlukları tekli boşluğa çevir
        text = ' '.join(text.split())
        return text.strip()

    def _is_product_line(self, line: str) -> bool:
        """Satırın ürün satırı olup olmadığını kontrol et"""
        # En az bir sayı ve metin içermeli
        if not re.search(r'\d+', line) or not re.search(r'[a-zA-Z]', line):
            return False
            
        # Fiyat benzeri bir değer içermeli
        if not re.search(r'\d+(?:\.\d{2})?', line):
            return False
            
        return True

    def _parse_product_line(self, line: str) -> ProductItem:
        """Ürün satırını ayrıştır"""
        product = ProductItem()
        
        try:
            # Önce kod ve miktar bulmaya çalış
            code_match = re.search(r'^(\w+)', line)
            if code_match and len(code_match.group(1)) >= 4:
                product.code = code_match.group(1)
                line = line[len(product.code):].strip()
            
            # Miktarı bul
            qty_match = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:PC|PCS|ADET|SET)?\b', line)
            if qty_match:
                product.quantity = float(qty_match.group(1))
                
            # Birim fiyatı bul
            price_match = re.search(r'(\d+(?:\.\d{2})?)\s*$', line)
            if price_match:
                product.unit_price = Decimal(price_match.group(1))
                
            # Açıklamayı al (kod ve fiyat arasındaki kısım)
            desc_start = len(product.code) if product.code else 0
            desc_end = line.rfind(str(product.unit_price)) if product.unit_price else len(line)
            product.description = line[desc_start:desc_end].strip()
            
            # Birimi bul
            for unit_name, pattern in self.unit_patterns.items():
                if re.search(pattern, product.description, re.IGNORECASE):
                    product.unit = unit_name
                    break
            
            # Toplam tutarı hesapla
            if product.quantity and product.unit_price:
                product.total = Decimal(str(product.quantity)) * product.unit_price
                
        except Exception as e:
            self.logger.error(f"Error parsing product line: {line} - {str(e)}")
            
        return product

    def _is_continuation_line(self, line: str) -> bool:
        """Satırın önceki ürünün devamı olup olmadığını kontrol et"""
        # Sadece metin içermeli, sayı veya fiyat olmamalı
        return bool(re.match(r'^[a-zA-Z\s\-\/]+$', line))

    def _normalize_quantity(self, qty_str: str) -> float:
        """Miktar değerini normalize et"""
        try:
            # Virgülü noktaya çevir
            qty_str = qty_str.replace(',', '.')
            return float(qty_str)
        except ValueError:
            return 0.0

    def _normalize_price(self, price_str: str) -> Decimal:
        """Fiyat değerini normalize et"""
        try:
            # Gereksiz karakterleri temizle
            price_str = re.sub(r'[^\d.,]', '', price_str)
            # Virgülü noktaya çevir
            price_str = price_str.replace(',', '.')
            return Decimal(price_str)
        except:
            return Decimal('0') 