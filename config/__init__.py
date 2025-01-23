from .development import DevelopmentConfig
from .production import ProductionConfig

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 