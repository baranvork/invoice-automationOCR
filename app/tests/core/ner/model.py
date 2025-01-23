import spacy
import logging
from typing import Dict, Any, List
import re
from datetime import datetime
from flask import current_app

class NERModel:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._nlp = None
        
        # Özel entity patterns
        self.patterns = [
            {"label": "VENDOR", "pattern": [{"TEXT": {"REGEX": "^[A-Z][A-Za-z\s]+(?:Ltd|Inc|LLC|Co\.|Company|A\.Ş\.|Limited)$"}}]},
            {"label": "TAX_ID", "pattern": [{"TEXT": {"REGEX": "^[A-Z0-9-]{10,15}$"}}]},
            {"label": "AMOUNT", "pattern": [{"TEXT": {"REGEX": "\d+[.,]\d{2}"}}]},
            {"label": "ADDRESS", "pattern": [{"TEXT": {"REGEX": ".*NO.*?/.*"}}]},
        ]

    @property
    def nlp(self):
        if self._nlp is None:
            try:
                self._nlp = spacy.load("en_core_web_lg")
                
                # Özel entity ruler ekle
                ruler = self._nlp.add_pipe("entity_ruler", before="ner")
                ruler.add_patterns(self.patterns)
                
            except:
                spacy.cli.download("en_core_web_lg")
                self._nlp = spacy.load("en_core_web_lg")
        return self._nlp

    def process_text(self, text: str) -> Dict[str, Any]:
        try:
            doc = self.nlp(text)
            entities = self._extract_entities(doc)
            
            # Özel entity işleme
            custom_entities = self._process_custom_entities(text)
            
            # Sonuçları birleştir
            for key, values in custom_entities.items():
                if key in entities:
                    entities[key].extend(values)
                else:
                    entities[key] = values
            
            return {
                'entities': entities,
                'success': True
            }
        except Exception as e:
            self.logger.error(f"NER Error: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _extract_entities(self, doc) -> Dict[str, list]:
        entities = {
            'organizations': [],
            'dates': [],
            'amounts': [],
            'locations': [],
            'tax_ids': [],
            'addresses': []
        }
        
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                entities['organizations'].append(ent.text)
            elif ent.label_ == 'DATE':
                entities['dates'].append(ent.text)
            elif ent.label_ == 'MONEY':
                entities['amounts'].append(ent.text)
            elif ent.label_ in ['GPE', 'LOC']:
                entities['locations'].append(ent.text)
            elif ent.label_ == 'TAX_ID':
                entities['tax_ids'].append(ent.text)
            elif ent.label_ == 'ADDRESS':
                entities['addresses'].append(ent.text)
        
        return {k: list(set(v)) for k, v in entities.items()}

    def _process_custom_entities(self, text: str) -> Dict[str, List[str]]:
        """Özel entity işleme"""
        custom_entities = {
            'tax_ids': [],
            'addresses': [],
            'amounts': []
        }
        
        # Vergi numarası
        tax_pattern = r'(?i)(?:tax\s+id|vat\s+no|gstin)\s*:\s*([A-Z0-9-]+)'
        if matches := re.finditer(tax_pattern, text):
            custom_entities['tax_ids'].extend(m.group(1) for m in matches)
        
        # Adres
        address_pattern = r'(?i)(?:address\s*:\s*([^\n]+)|.*NO.*?/.*)'
        if matches := re.finditer(address_pattern, text):
            custom_entities['addresses'].extend(m.group(1) if m.group(1) else m.group(0) for m in matches)
        
        # Para miktarları
        amount_pattern = r'(?i)(?:total|amount|balance)\s*:?\s*(?:TL|₺|USD|\$|EUR|€)?\s*(\d+(?:[.,]\d{2})?)'
        if matches := re.finditer(amount_pattern, text):
            custom_entities['amounts'].extend(m.group(1) for m in matches)
        
        return custom_entities 