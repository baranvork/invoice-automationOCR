import logging
import numpy as np
from typing import Dict, Any, List, Optional, Union
import tensorflow.types.experimental as tf_types  # Tip tanımlamaları için
import traceback

class TensorFlowProcessor:
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
        
        self._tf = None
        self._keras_ocr = None
        self._bert_tokenizer = None
        self._bert_model = None
        self._ocr_pipeline = None
        
    @property
    def tf(self):
        if self._tf is None:
            import tensorflow as tf
            self._tf = tf
        return self._tf
        
    @property
    def keras_ocr(self):
        if self._keras_ocr is None:
            import keras_ocr
            self._keras_ocr = keras_ocr
        return self._keras_ocr

    def process_document(self, image: np.ndarray) -> Dict[str, Any]:
        """Belgeyi işle"""
        self.logger.info("=== DOCUMENT PROCESSING STARTED ===")
        try:
            # TensorFlow session'ı temizle
            self.tf.keras.backend.clear_session()
            
            # GPU kontrolü
            gpus = self.tf.config.experimental.list_physical_devices('GPU')
            if gpus:
                self.logger.info(f"GPU detected: {gpus}")
            else:
                self.logger.info("Using CPU for processing")
            
            # Lazy loading için None ile başlat
            self._ocr_pipeline = None
            self._bert_model = None
            self._tokenizer = None
            
            # GPU kontrolü ve seçimi
            device = '/GPU:0' if self.tf.test.is_built_with_cuda() else '/CPU:0'
            self.logger.info(f"Using device: {device}")
            
            with self.tf.device(device):
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
                
                # Metin analizi
                self.logger.info("\n=== NER PROCESSING ===")
                entities = self._extract_entities(ocr_results['text'])
                
                self.logger.info(f"""
Extracted Entities:
-----------------
{entities}
                """)
                
                # Tablo analizi
                self.logger.info("\n=== TABLE ANALYSIS ===")
                tables = self._analyze_tables(image)
                
                self.logger.info(f"""
Table Analysis Results:
---------------------
Tables Found: {len(tables)}
                """)
                
                results = {
                    'success': True,
                    'ocr': ocr_results,
                    'entities': entities,
                    'tables': tables,
                    'confidence': self._calculate_confidence(ocr_results, entities)
                }
                
                self.logger.info("\n=== PROCESSING COMPLETED ===")
                self.logger.info(f"""
Final Results:
-------------
Overall Confidence: {results['confidence']:.2f}%
Success: {results['success']}
                """)
                
                return results
                
        except Exception as e:
            self.logger.error(f"""
Processing Error:
---------------
Error Type: {type(e).__name__}
Error Message: {str(e)}
                """)
            return {'success': False, 'error': str(e)}
            
        finally:
            self.tf.keras.backend.clear_session()

    @property
    def ocr_pipeline(self):
        """OCR pipeline'ı lazy loading ile yükle"""
        if self._ocr_pipeline is None:
            try:
                self.logger.info("Initializing OCR pipeline...")
                import keras_ocr
                self._ocr_pipeline = keras_ocr.pipeline.Pipeline()
                self.logger.info("OCR pipeline initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing OCR pipeline: {str(e)}")
                raise
        return self._ocr_pipeline
    
    @property
    def bert_model(self) -> Any:
        """BERT modelini lazy loading ile yükle"""
        if self._bert_model is None:
            self._bert_model = self.tf.keras.applications.BertForTokenClassification.from_pretrained(
                'bert-base-multilingual-cased',
                from_pt=True
            )
        return self._bert_model
    
    @property
    def tokenizer(self) -> Any:
        """BERT tokenizer'ı lazy loading ile yükle"""
        if self._tokenizer is None:
            self._tokenizer = self.tf.keras.preprocessing.text.Tokenizer(
                char_level=False,
                oov_token='[UNK]',
                filters='',
                lower=False,
                split=' ',
                auto_lower=True,
                auto_stem=True,
                preprocessor=None,
                postprocessor=None
            )
            self._tokenizer.fit_on_texts([
                ' '.join(self.ocr_pipeline.recognize([image])[0][i][0] for i in range(len(self.ocr_pipeline.recognize([image])[0])))
                for image in [image] * 100  # Assuming a large number of images for training
            ])
        return self._tokenizer

    def _perform_ocr(self, image: np.ndarray) -> Optional[Dict[str, Any]]:
        """KerasOCR ile metin tanıma"""
        try:
            self.logger.info("Starting OCR text recognition...")
            
            # Görüntü boyutlarını kontrol et
            self.logger.info(f"Image shape: {image.shape}")
            
            # Görüntüyü normalize et
            if image.dtype != np.uint8:
                image = (image * 255).astype(np.uint8)
            
            # OCR pipeline'ı kullan
            pipeline = self.ocr_pipeline  # property üzerinden al
            
            # Görüntüyü işle
            self.logger.info("Running OCR recognition...")
            predictions = pipeline.recognize([image])
            
            if not predictions:
                raise ValueError("No text detected in image")
            
            text_blocks = []
            coordinates = []
            confidences = []
            
            self.logger.info("\nDetected Text Blocks:")
            self.logger.info("-" * 50)
            
            # İlk tahmin listesini al
            for idx, (text, box) in enumerate(predictions[0]):
                text_blocks.append(text)
                coordinates.append(box.tolist())
                conf = np.mean([coord[1] for coord in box])
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

    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """BERT ile varlık tanıma"""
        try:
            # Tokenization
            inputs = self.tokenizer.texts_to_sequences([text])
            inputs = self.tf.keras.preprocessing.sequence.pad_sequences(inputs, maxlen=128)
            
            # BERT analizi
            outputs = self.bert_model(inputs)
            
            # Tahminleri işle
            predictions = self.tf.nn.softmax(outputs.logits, axis=-1)
            labels = self.tf.argmax(predictions, axis=-1)
            
            return self._process_predictions(labels, inputs, predictions)
            
        except Exception as e:
            self.logger.error(f"Entity extraction error: {str(e)}")
            return {}

    def _analyze_tables(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Tablo analizi"""
        try:
            # Görüntüyü hazırla
            image = self.tf.convert_to_tensor(image)
            image = self.tf.image.resize(image, [640, 640])
            
            # Basit tablo tespiti
            gray = self.tf.image.rgb_to_grayscale(image)
            edges = self.tf.image.sobel_edges(gray)
            
            return self._process_table_detection(edges)
            
        except Exception as e:
            self.logger.error(f"Table analysis error: {str(e)}")
            return []

    def _calculate_confidence(self, ocr_results: Dict[str, Any], 
                            entities: Dict[str, Any]) -> float:
        """Genel güven skorunu hesapla"""
        scores = [
            ocr_results.get('confidence', 0),
            entities.get('confidence', 0) if entities else 0
        ]
        return float(np.mean(scores)) if scores else 0.0

    def _process_predictions(self, 
                           labels: Union[np.ndarray, Any],
                           inputs: Union[np.ndarray, Any], 
                           predictions: Union[np.ndarray, Any]) -> Dict[str, Any]:
        """BERT tahminlerini işle"""
        try:
            # Token'ları kelimelere dönüştür
            tokens = self.tokenizer.sequences_to_texts([inputs[0].numpy()])[0]
            
            # Etiketleri eşle
            results = {}
            current_entity = []
            current_label = None
            
            for token, label, conf in zip(tokens, 
                                        labels[0].numpy(), 
                                        predictions[0].numpy()):
                if label > 0:  # 0 = O (other) etiketi değil
                    if current_label != label:
                        if current_entity:
                            results[current_label] = ' '.join(current_entity)
                        current_entity = [token]
                        current_label = label
                    else:
                        current_entity.append(token)
                        
            return results
            
        except Exception as e:
            self.logger.error(f"Prediction processing error: {str(e)}")
            return {} 