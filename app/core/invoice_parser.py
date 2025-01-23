import re
from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal

@dataclass
class InvoiceProduct:
    code: str
    description: str
    quantity: float
    unit_price: Decimal
    total: Decimal

@dataclass
class Invoice:
    # Temel bilgiler
    sender_company: str
    sender_address: str
    recipient_company: str
    invoice_date: str
    invoice_number: str
    
    # Finansal bilgiler
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    
    # Ürün listesi
    products: List[InvoiceProduct]

class InvoiceParser:
    def parse(self, text: str) -> Invoice:
        lines = text.split('\n')
        
        # 1. Şirket bilgilerini çıkar
        sender = self._extract_sender(lines[:8])  # İlk 8 satıra bak
        recipient = self._extract_recipient(lines[8:12])  # Sonraki 4 satıra bak
        
        # 2. Ürünleri çıkar
        products = self._extract_products(lines)
        
        # 3. Tutarları çıkar
        amounts = self._extract_amounts(lines)
        
        # 4. Tarihi çıkar
        date = self._extract_date(text)
        
        # 5. Fatura numarasını çıkar
        invoice_number = self._extract_invoice_number(text)
        
        return Invoice(
            sender_company=sender['company'],
            sender_address=sender['address'],
            recipient_company=recipient,
            invoice_date=date,
            invoice_number=invoice_number,
            subtotal=amounts['subtotal'],
            tax=amounts['tax'],
            total=amounts['total'],
            products=products
        )
    
    def _extract_sender(self, lines: List[str]) -> dict:
        """Gönderen şirket bilgilerini çıkar"""
        company = None
        address_parts = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Şirket adını bul
            if 'PERNIAGAAN' in line:
                company = line
                continue
            
            # Adres satırlarını topla
            if any(keyword in line.upper() for keyword in ['JALAN', 'BANDAR', 'TEL', 'FAX', 'GST NO']):
                address_parts.append(line)
        
        return {
            'company': company,
            'address': ', '.join(address_parts)
        }
    
    def _extract_recipient(self, lines: List[str]) -> str:
        """Alıcı şirket adını çıkar"""
        for line in lines:
            if 'ENGINEERING' in line.upper():
                return line.strip()
        return None
    
    def _extract_products(self, lines: List[str]) -> List[InvoiceProduct]:
        """Ürün listesini çıkar"""
        products = []
        current_product = None
        
        for line in lines:
            line = line.strip()
            
            # Ürün kodu ve fiyat satırı
            if match := re.match(r'(\d+)\s+(\d+)\s+(\d+\.\d{2})', line):
                if current_product:
                    products.append(current_product)
                
                code, qty, price = match.groups()
                current_product = InvoiceProduct(
                    code=code,
                    description='',  # Sonraki satırda doldurulacak
                    quantity=float(qty),
                    unit_price=Decimal(price),
                    total=Decimal(price) * Decimal(qty)
                )
            
            # Ürün açıklaması
            elif current_product and 'SR' in line:
                desc = re.sub(r'^SR[:\.]?\s*', '', line)
                current_product.description = desc.strip()
        
        if current_product:
            products.append(current_product)
        
        return products
    
    def _extract_amounts(self, lines: List[str]) -> dict:
        """Tutarları çıkar"""
        amounts = {
            'subtotal': Decimal('0'),
            'tax': Decimal('0'),
            'total': Decimal('0')
        }
        
        for line in lines:
            line = line.strip().upper()
            
            # Alt toplam
            if '(EXCLUDED GST) SUB' in line:
                if match := re.search(r'(\d+\.\d{2})', line):
                    amounts['subtotal'] = Decimal(match.group(1))
            
            # Vergi
            elif 'GST' in line and not 'GST NO' in line:
                if match := re.search(r'(\d+\.\d{2})', line):
                    amounts['tax'] = Decimal(match.group(1))
            
            # Toplam
            elif 'TOTAL (RM)' in line or 'CASH' in line:
                if match := re.search(r'(\d+\.\d{2})', line):
                    amounts['total'] = Decimal(match.group(1))
        
        return amounts
    
    def _extract_date(self, text: str) -> str:
        """Fatura tarihini çıkar"""
        if match := re.search(r'Date\s*:\s*(\d{2}/\d{2}/\d{4})', text):
            return match.group(1)
        return None
    
    def _extract_invoice_number(self, text: str) -> str:
        """Fatura numarasını çıkar"""
        if match := re.search(r'Receipt#\s*:\s*(\w+)', text):
            return match.group(1)
        return None 