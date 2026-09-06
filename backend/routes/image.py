# ==============================================================
# Image Compressor Route
# POST /api/image/compress  → multipart form → compressed image
# ==============================================================

from flask import Blueprint, request, jsonify, send_file
from PIL import Image
import io
import os

image_bp = Blueprint('image', __name__)

ALLOWED_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
MAX_SIZE_MB = 20

@image_bp.route('/compress', methods=['POST'])
def compress():
    if 'image' not in request.files:
        return jsonify({'error': 'Image file provide karein'}), 400

    file    = request.files['image']
    quality = int(request.form.get('quality', 75))
    fmt     = request.form.get('format', 'JPEG').upper()

    if file.content_type not in ALLOWED_TYPES:
        return jsonify({'error': 'Only JPG, PNG, WebP images allowed'}), 400

    quality = max(10, min(95, quality))

    try:
        img_data = file.read()
        if len(img_data) > MAX_SIZE_MB * 1024 * 1024:
            return jsonify({'error': f'File too large. Max {MAX_SIZE_MB}MB allowed'}), 400

        img = Image.open(io.BytesIO(img_data))

        # Convert RGBA to RGB for JPEG
        if fmt == 'JPEG' and img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        output = io.BytesIO()
        img.save(output, format=fmt, quality=quality, optimize=True)
        output.seek(0)

        original_size   = len(img_data)
        compressed_size = output.getbuffer().nbytes
        savings_pct     = round((1 - compressed_size / original_size) * 100, 1)

        output.seek(0)
        mime = 'image/jpeg' if fmt == 'JPEG' else f'image/{fmt.lower()}'
        response = send_file(output, mimetype=mime, as_attachment=True,
                             download_name=f'compressed.{fmt.lower()}')
        response.headers['X-Original-Size']   = str(original_size)
        response.headers['X-Compressed-Size'] = str(compressed_size)
        response.headers['X-Savings-Pct']     = str(savings_pct)
        return response

    except Exception as e:
        return jsonify({'error': str(e)}), 500
