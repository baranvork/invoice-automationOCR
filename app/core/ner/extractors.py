# Entity çıkarıcılar
import re
import logging

class EntityExtractor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_amounts(self, text, patterns):
        """Tutarları daha esnek bir şekilde çıkar"""
        amounts = {'subtotal': None, 'taxes': None, 'total': None}
        
        # Tüm sayısal değerleri bul
        amount_matches = re.finditer(r'(?:RM)?\s*(\d+(?:[,.]\d{2})?)', text)
        found_amounts = [match.group(1).replace(',', '.') for match in amount_matches]
        
        if found_amounts:
            try:
                # Alt toplam genelde en büyük tutarlardan biri
                potential_subtotals = [float(amt) for amt in found_amounts if 50 < float(amt) < 1000]
                if potential_subtotals:
                    amounts['subtotal'] = f"RM {max(potential_subtotals):.2f}"

                # Vergi genelde küçük bir tutar
                potential_taxes = [float(amt) for amt in found_amounts if 0 < float(amt) < 20]
                if potential_taxes:
                    amounts['taxes'] = f"RM {min(potential_taxes):.2f}"

                # Toplam genelde alt toplam + vergi
                if amounts['subtotal'] and amounts['taxes']:
                    subtotal = float(amounts['subtotal'].replace('RM ', ''))
                    tax = float(amounts['taxes'].replace('RM ', ''))
                    total = subtotal + tax
                    amounts['total'] = f"RM {total:.2f}"

            except ValueError as e:
                self.logger.error(f"Error parsing amounts: {e}")

        return amounts

    def extract_companies(self, text, patterns):
        """Şirket isimlerini daha akıllı bir şekilde çıkar"""
        companies = {'sender': None, 'recipient': None}
        
        # Başlıktaki büyük harfli metinleri bul
        header_lines = text.split('\n')[:5]  # İlk 5 satıra bak
        company_candidates = []
        
        for line in header_lines:
            # Temizle ve kontrol et
            line = line.strip()
            if line.isupper() and len(line) > 3:  # En az 3 karakter
                company_candidates.append(line)
        
        if company_candidates:
            # İlk şirket genelde gönderen
            companies['sender'] = company_candidates[0]
            
            # Varsa ikinci şirket alıcı
            if len(company_candidates) > 1:
                companies['recipient'] = company_candidates[1]

        return companies

    def extract_addresses(self, text, patterns):
        """Adresleri daha akıllı bir şekilde çıkar"""
        addresses = {'sender': None, 'recipient': None}
        
        # Adres bileşenlerini bul
        address_parts = []
        
        # Satır satır kontrol et
        lines = text.split('\n')
        current_part = []
        
        for line in lines:
            line = line.strip()
            
            # Adres olabilecek satırları kontrol et
            if any(keyword in line.upper() for keyword in ['JALAN', 'ROAD', 'STREET', 'NO.', 'TEL', 'FAX']):
                current_part.append(line)
            # Posta kodu içeren satırlar
            elif re.search(r'\d{5}', line):
                current_part.append(line)
                address_parts.append(' '.join(current_part))
                current_part = []
            # Eyalet/şehir isimleri
            elif any(keyword in line.upper() for keyword in ['JOHOR', 'SELANGOR', 'KUALA LUMPUR', 'PENANG']):
                current_part.append(line)
                address_parts.append(' '.join(current_part))
                current_part = []
        
        if address_parts:
            # Gereksiz boşlukları temizle ve birleştir
            cleaned_address = ', '.join(part.strip() for part in address_parts if part.strip())
            addresses['sender'] = cleaned_address
        
        return addresses

    def extract_dates(self, text):
        """Tarihleri daha akıllı bir şekilde çıkar"""
        dates = {'invoice_date': None, 'due_date': None}
        
        # Tüm tarih formatlarını kontrol et
        date_patterns = [
            r'(?:Date|Tarih)\s*:?\s*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})',
            r'(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                dates['invoice_date'] = match.group(1)
                break
        
        return dates 