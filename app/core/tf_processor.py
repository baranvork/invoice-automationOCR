import logging
import numpy as np
from typing import Dict, Any, List, Optional
import tensorflow as tf
import keras_ocr
import traceback

class TensorFlowProcessor:
    def __init__(self):
        # Logging ayarları
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '\n%(asctime)s - %(name)s - %(levelname)s\n%(message)s\n'
        )
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        
        self._tf = None
        self._keras_ocr = None
        self._ocr_pipeline = None

    @property
    def tf(self):
        if self._tf is None:
            import tensorflow as tf
            # GPU bellek ayarları
            gpus = tf.config.experimental.list_physical_devices('GPU')
            if gpus:
                try:
                    for gpu in gpus:
                        tf.config.experimental.set_memory_growth(gpu, True)
                except RuntimeError as e:
                    self.logger.error(f"GPU configuration error: {e}")
            self._tf = tf
        return self._tf

    @property
    def ocr_pipeline(self):
        """KerasOCR pipeline'ı lazy loading ile yükle"""
        if self._ocr_pipeline is None:
            try:
                self.logger.info("Initializing OCR pipeline...")
                self._ocr_pipeline = keras_ocr.pipeline.Pipeline(
                    detector='db_resnet50',
                    recognizer='crnn_vgg16_bn',
                    scale=2,
                    max_size=2048
                )
                self.logger.info("OCR pipeline initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing OCR pipeline: {str(e)}")
                raise
        return self._ocr_pipeline

    def process_document(self, image: np.ndarray) -> Dict[str, Any]:
        """Belgeyi işle"""
        self.logger.info("=== DOCUMENT PROCESSING STARTED ===")
        try:
            # TensorFlow session'ı temizle
            self.tf.keras.backend.clear_session()
            
            # GPU kontrolü
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
                
                results = {
                    'success': True,
                    'ocr': ocr_results,
                    'confidence': ocr_results['confidence']
                }
                
                self.logger.info("\n=== PROCESSING COMPLETED ===")
                return results
                
        except Exception as e:
            self.logger.error(f"""
Processing Error:
---------------
Error Type: {type(e).__name__}
Error Message: {str(e)}
Stack Trace: {traceback.format_exc()}
            """)
            return {'success': False, 'error': str(e)}
            
        finally:
            self.tf.keras.backend.clear_session()

    def _perform_ocr(self, image: np.ndarray) -> Optional[Dict[str, Any]]:
        """KerasOCR ile metin tanıma"""
        try:
            self.logger.info("Starting OCR text recognition...")
            
            # Görüntü boyutlarını kontrol et
            self.logger.info(f"Image shape: {image.shape}")
            
            # Görüntüyü normalize et
            if image.dtype != np.uint8:
                image = (image * 255).astype(np.uint8)
            
            # OCR işlemi
            self.logger.info("Running OCR recognition...")
            predictions = self.ocr_pipeline.recognize([image])
            
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