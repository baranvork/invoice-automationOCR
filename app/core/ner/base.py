import logging
import spacy

# Temel NER sınıfı
class BaseNERModel:
    def __init__(self):
        self._setup_logging()
        self._load_models()
        
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def _load_models(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.logger.info("Downloading SpaCy model...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm") 