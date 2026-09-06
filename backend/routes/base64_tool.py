# ==============================================================
# Base64 Encoder/Decoder Route
# POST /api/base64/encode  → { text }    → { encoded }
# POST /api/base64/decode  → { encoded } → { decoded }
# POST /api/base64/encode-file → multipart → { encoded }
# ==============================================================

from flask import Blueprint, request, jsonify
import base64

base64_bp = Blueprint('base64', __name__)

@base64_bp.route('/encode', methods=['POST'])
def encode():
    data = request.get_json()
    text = (data or {}).get('text', '')

    if not text:
        return jsonify({'error': 'Text provide karein'}), 400

    try:
        encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        return jsonify({
            'encoded':        encoded,
            'original_length': len(text),
            'encoded_length':  len(encoded),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@base64_bp.route('/decode', methods=['POST'])
def decode():
    data    = request.get_json()
    encoded = (data or {}).get('encoded', '').strip()

    if not encoded:
        return jsonify({'error': 'Encoded string provide karein'}), 400

    try:
        # Fix padding if needed
        encoded += '=' * (-len(encoded) % 4)
        decoded = base64.b64decode(encoded).decode('utf-8')
        return jsonify({
            'decoded':        decoded,
            'encoded_length': len(encoded),
            'decoded_length': len(decoded),
        })
    except Exception:
        return jsonify({'error': 'Invalid Base64 string hai. Check karein'}), 400


@base64_bp.route('/encode-file', methods=['POST'])
def encode_file():
    if 'file' not in request.files:
        return jsonify({'error': 'File provide karein'}), 400

    file = request.files['file']
    try:
        file_bytes = file.read()
        if len(file_bytes) > 5 * 1024 * 1024:  # 5MB limit
            return jsonify({'error': 'File too large. Max 5MB allowed'}), 400

        encoded = base64.b64encode(file_bytes).decode('utf-8')
        # Detect MIME type for data URI
        mime = file.content_type or 'application/octet-stream'
        data_uri = f'data:{mime};base64,{encoded}'

        return jsonify({
            'encoded':   encoded,
            'data_uri':  data_uri,
            'mime_type': mime,
            'filename':  file.filename,
            'file_size': len(file_bytes),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
