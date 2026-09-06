# ==============================================================
# PDF Tools Route
# POST /api/pdf/info  → multipart form → PDF metadata
# ==============================================================

from flask import Blueprint, request, jsonify
import pdfplumber
import PyPDF2
import io

pdf_bp = Blueprint('pdf', __name__)

@pdf_bp.route('/info', methods=['POST'])
def pdf_info():
    if 'pdf' not in request.files:
        return jsonify({'error': 'PDF file provide karein'}), 400

    file = request.files['pdf']
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Sirf PDF files allowed hain'}), 400

    try:
        pdf_bytes = file.read()
        reader    = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        meta      = reader.metadata or {}

        # Basic info
        info = {
            'page_count':  len(reader.pages),
            'title':       meta.get('/Title', 'N/A'),
            'author':      meta.get('/Author', 'N/A'),
            'subject':     meta.get('/Subject', 'N/A'),
            'creator':     meta.get('/Creator', 'N/A'),
            'producer':    meta.get('/Producer', 'N/A'),
            'created':     str(meta.get('/CreationDate', 'N/A')),
            'modified':    str(meta.get('/ModDate', 'N/A')),
            'encrypted':   reader.is_encrypted,
            'file_size':   len(pdf_bytes),
        }

        # Extract text from first 3 pages
        preview_text = ''
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for i, page in enumerate(pdf.pages[:3]):
                    text = page.extract_text() or ''
                    preview_text += text + '\n\n'
                    if i == 0:
                        # Get page dimensions
                        info['page_width']  = round(page.width, 2)
                        info['page_height'] = round(page.height, 2)
        except Exception:
            pass

        info['text_preview'] = preview_text[:1000].strip()
        info['word_count']   = len(preview_text.split())

        return jsonify(info)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
