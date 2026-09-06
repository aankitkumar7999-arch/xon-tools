# ==============================================================
# ToolsHub Backend — Flask Main App
# Run: python app.py
# API Base: http://localhost:5000/api
# ==============================================================

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=False)


# ── Import & Register all route blueprints ──
from routes.youtube    import youtube_bp
from routes.image      import image_bp
from routes.pdf        import pdf_bp
from routes.text       import text_bp
from routes.qr         import qr_bp
from routes.password   import password_bp
from routes.converter  import converter_bp
from routes.age        import age_bp
from routes.base64_tool import base64_bp

app.register_blueprint(youtube_bp,   url_prefix='/api/youtube')
app.register_blueprint(image_bp,     url_prefix='/api/image')
app.register_blueprint(pdf_bp,       url_prefix='/api/pdf')
app.register_blueprint(text_bp,      url_prefix='/api/text')
app.register_blueprint(qr_bp,        url_prefix='/api/qr')
app.register_blueprint(password_bp,  url_prefix='/api/password')
app.register_blueprint(converter_bp, url_prefix='/api/convert')
app.register_blueprint(age_bp,       url_prefix='/api/age')
app.register_blueprint(base64_bp,    url_prefix='/api/base64')

# ── Health Check ──
@app.route('/api/health')
def health():
    return {'status': 'ok', 'message': 'ToolsHub Backend Running!'}


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    port = int(os.environ.get('PORT', 5000))
    is_prod = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT')
    print("\nXON Tools Backend Starting...")
    print(f"API Base: http://localhost:{port}/api")
    print(f"Health:   http://localhost:{port}/api/health\n")
    app.run(debug=not is_prod, port=port, host='0.0.0.0')

