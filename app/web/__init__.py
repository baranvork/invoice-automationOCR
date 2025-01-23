from flask import Blueprint

# Blueprint'i burada tanımlama, routes.py'den import et
from .routes import web_bp

__all__ = ['web_bp'] 