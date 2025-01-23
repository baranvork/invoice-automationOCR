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

def enhance_image(image):
    """
    Görüntü iyileştirme fonksiyonu
    """
    # Kontrast artırma
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(image)
    
    return enhanced 