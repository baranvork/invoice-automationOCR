import cv2
import numpy as np

def preprocess_image(image):
    """
    Görüntü ön işleme fonksiyonu
    """
    # Gri tonlamaya çevir
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Gürültü azaltma
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # Adaptif eşikleme
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    return thresh

def allowed_file(filename, allowed_extensions):
    """
    Dosya uzantısı kontrolü
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions 