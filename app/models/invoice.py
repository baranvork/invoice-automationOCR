from datetime import datetime
from app import db

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))  # Dosya adını saklamak için yeni alan
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    vendor = db.Column(db.String(200))
    amount = db.Column(db.Float)
    category = db.Column(db.String(50))
    invoice_number = db.Column(db.String(100))
    tax_id = db.Column(db.String(100))
    tax_amount = db.Column(db.Float)
    raw_text = db.Column(db.Text)
    confidence = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 