# ==============================================================
# QR Code Generator Route
# POST /api/qr/generate  → { text, size, color, bg } → PNG image
# ==============================================================

from flask import Blueprint, request, jsonify, send_file
import qrcode
from qrcode.image.styledpil import StyledPilImage
from PIL import Image
import io
import base64

qr_bp = Blueprint('qr', __name__)

@qr_bp.route('/generate', methods=['POST'])
def generate():
    data  = request.get_json()
    text  = (data or {}).get('text', '').strip()
    size  = int((data or {}).get('size', 300))
    color = (data or {}).get('color', '#000000')
    bg    = (data or {}).get('bg', '#FFFFFF')

    if not text:
        return jsonify({'error': 'Text ya URL provide karein'}), 400

    size = max(100, min(1000, size))

    try:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)

        def hex_to_rgb(h):
            h = h.lstrip('#')
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        fill_color = hex_to_rgb(color) if color.startswith('#') else (0, 0, 0)
        back_color = hex_to_rgb(bg)    if bg.startswith('#')    else (255, 255, 255)

        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        img = img.resize((size, size), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)

        # Return as base64 so JS can display it directly
        img_b64 = base64.b64encode(buf.read()).decode('utf-8')
        return jsonify({
            'image': f'data:image/png;base64,{img_b64}',
            'text':  text,
            'size':  size,
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
