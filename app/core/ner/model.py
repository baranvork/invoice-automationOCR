import logging
from .base import BaseNERModel
from .patterns import AMOUNT_PATTERNS, ADDRESS_PATTERNS, COMPANY_KEYWORDS
from .extractors import EntityExtractor
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

class NERModel(BaseNERModel):
    def __init__(self):
        super().__init__()
        self.extractor = EntityExtractor()
        self.patterns = {
            'amount': AMOUNT_PATTERNS,
            'address': ADDRESS_PATTERNS,
            'company': COMPANY_KEYWORDS
        }

    def extract_entities(self, text):
        if not isinstance(text, str):
            return None
            
        cleaned_text = self._clean_text(text)
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_amounts = executor.submit(
                self.extractor.extract_amounts, 
                cleaned_text, 
                self.patterns['amount']
            )
            future_addresses = executor.submit(
                self.extractor.extract_addresses, 
                cleaned_text, 
                self.patterns['address']
            )
            
            results = {
                'amounts': future_amounts.result(),
                'addresses': {
                    'sender': future_addresses.result(),
                    'recipient': None
                },
                'companies': {'sender': None, 'recipient': None},
                'dates': {'invoice_date': None, 'due_date': None}
            }
            
        return results

    @lru_cache(maxsize=100)
    def _clean_text(self, text):
        return ' '.join(text.split()) 