from flask import Blueprint, render_template, request, jsonify, current_app, url_for
from werkzeug.utils import secure_filename
import os
from app.core.document_processor import DocumentProcessor
from app.utils.file_helpers import allowed_file
import logging
from app.models.invoice import Invoice
from app import db
from datetime import datetime

# Blueprint'i doğru şekilde tanımla
web_bp = Blueprint('web', __name__, 
                  template_folder='templates',  # templates klasörünün yolu
                  static_folder='static',       # static klasörünün yolu
                  url_prefix='/')              # URL prefix'i

logger = logging.getLogger(__name__)

# Ana sayfa
@web_bp.route('/')
@web_bp.route('/index')
def index():
    try:
        # Mevcut faturaları getir
        invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
        
        # Fatura verilerini hazırla
        for invoice in invoices:
            # Timestamp'i oluştur
            timestamp = invoice.date.strftime('%Y%m%d_%H%M%S')
            # Dosya adını oluştur
            if not invoice.filename:  # Eğer filename boşsa
                invoice.filename = f"{timestamp}_invoice.pdf"  # Varsayılan bir isim ver
        
        return render_template('index.html', invoices=invoices)
    except Exception as e:
        current_app.logger.error(f"Error rendering index: {str(e)}")
        return str(e), 500

# Fatura yükleme
@web_bp.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file part'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'})
        
        if file and allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
            # Benzersiz dosya adı oluştur
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            original_filename = secure_filename(file.filename)
            filename = f"{timestamp}_{original_filename}"
            
            # Dosyayı static/uploads/permanent klasörüne kaydet
            upload_dir = os.path.join('app', 'static', 'uploads', 'permanent')
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            
            try:
                file.save(file_path)
                processor = DocumentProcessor(current_app.config)
                result = processor.process_document(file_path)
                
                # OCR sonuçlarını logla
                current_app.logger.info(f"OCR Result: {result}")
                
                if not result or not result.get('invoice_data'):
                    return jsonify({'success': False, 'error': 'OCR processing failed'})

                invoice_data = result.get('invoice_data', {})
                
                # Güvenli bir şekilde string değerlerini al
                def safe_str(value, default=''):
                    if value is None:
                        return default
                    return str(value).strip()

                # Güvenli bir şekilde float değerlerini al
                def safe_float(value, default=0.0):
                    try:
                        if value is None:
                            return default
                        if isinstance(value, str):
                            value = value.replace(',', '.').replace('€', '').replace('RM', '').strip()
                        return float(value)
                    except (ValueError, TypeError):
                        return default

                # OCR sonuçlarından tarihi parse et
                date_str = invoice_data.get('date')
                if date_str:
                    try:
                        date = datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        try:
                            date = datetime.strptime(date_str, '%d/%m/%Y')
                        except ValueError:
                            date = datetime.now()
                else:
                    date = datetime.now()

                # Faturayı veritabanına kaydet
                invoice = Invoice(
                    filename=filename,
                    date=date,
                    vendor=safe_str(invoice_data.get('vendor')),
                    amount=safe_float(invoice_data.get('total_amount')),
                    category=safe_str(invoice_data.get('category'), 'others'),
                    invoice_number=safe_str(invoice_data.get('invoice_number')),
                    tax_id=safe_str(invoice_data.get('tax_id')),
                    tax_amount=safe_float(invoice_data.get('tax_amount')),
                    raw_text=safe_str(result.get('text')),
                    confidence=result.get('confidence', 0)
                )

                # Eğer vendor boşsa, raw text'ten tahmin et
                if not invoice.vendor:
                    lines = invoice.raw_text.split('\n')[:5]  # İlk 5 satıra bak
                    for line in lines:
                        if len(line) > 3 and not line.startswith(('Invoice', 'Date', 'Amount')):
                            invoice.vendor = line.strip()
                            break

                db.session.add(invoice)
                db.session.commit()

                # Dosya URL'sini oluştur
                file_url = url_for('static', filename=f'uploads/permanent/{filename}')

                return jsonify({
                    'success': True,
                    'invoice_id': invoice.id,
                    'filename': filename,
                    'file_url': file_url,
                    'text': result.get('text', ''),
                    'invoice_data': {
                        'date': invoice.date.strftime('%d/%m/%Y'),
                        'vendor': invoice.vendor,
                        'amount': f"{invoice.amount:.2f}",
                        'category': invoice.category,
                        'invoice_number': invoice.invoice_number,
                        'tax_id': invoice.tax_id,
                        'tax_amount': f"{invoice.tax_amount:.2f}",
                        'raw_text': invoice.raw_text
                    }
                })
                
            except Exception as e:
                current_app.logger.error(f"Error processing invoice: {str(e)}")
                return jsonify({'success': False, 'error': str(e)})
            finally:
                # Artık dosyayı silmiyoruz
                pass
        
        return jsonify({'success': False, 'error': 'Invalid file type'})
        
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@web_bp.route('/reset-db')
def reset_db():
    try:
        # Tüm tabloları sil ve yeniden oluştur
        db.drop_all()
        db.create_all()
        return 'Database reset successfully'
    except Exception as e:
        return str(e), 500

@web_bp.route('/delete/<int:invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    try:
        # Faturayı bul
        invoice = Invoice.query.get_or_404(invoice_id)
        
        # Dosyayı sil
        file_path = os.path.join('app', 'static', 'uploads', 'permanent', invoice.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Veritabanından sil
        db.session.delete(invoice)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Invoice deleted successfully'})
    except Exception as e:
        current_app.logger.error(f"Error deleting invoice: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 