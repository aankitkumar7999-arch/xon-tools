# ==============================================================
# Password Generator Route
# GET /api/password/generate?length=16&upper=1&lower=1&nums=1&symbols=1
# ==============================================================

from flask import Blueprint, request, jsonify
import secrets
import string

password_bp = Blueprint('password', __name__)

@password_bp.route('/generate', methods=['GET'])
def generate():
    try:
        length  = int(request.args.get('length',  16))
        upper   = request.args.get('upper',   '1') == '1'
        lower   = request.args.get('lower',   '1') == '1'
        nums    = request.args.get('nums',    '1') == '1'
        symbols = request.args.get('symbols', '1') == '1'
        count   = int(request.args.get('count', 5))

        length = max(4, min(128, length))
        count  = max(1, min(20,  count))

        charset = ''
        if upper:   charset += string.ascii_uppercase
        if lower:   charset += string.ascii_lowercase
        if nums:    charset += string.digits
        if symbols: charset += '!@#$%^&*()_+-=[]{}|;:,.<>?'

        if not charset:
            return jsonify({'error': 'At least ek character type select karein'}), 400

        passwords = []
        for _ in range(count):
            while True:
                pwd = ''.join(secrets.choice(charset) for _ in range(length))
                # Ensure at least one of each selected type
                ok = True
                if upper   and not any(c in string.ascii_uppercase for c in pwd): ok = False
                if lower   and not any(c in string.ascii_lowercase for c in pwd): ok = False
                if nums    and not any(c in string.digits for c in pwd):           ok = False
                if symbols and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in pwd): ok = False
                if ok:
                    passwords.append(pwd)
                    break

        # Strength score
        strength = 0
        if length >= 8:  strength += 1
        if length >= 12: strength += 1
        if length >= 16: strength += 1
        if upper and lower: strength += 1
        if nums:            strength += 1
        if symbols:         strength += 1
        strength_label = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong', 'Very Strong'][min(strength, 5)]

        return jsonify({
            'passwords':       passwords,
            'length':          length,
            'strength':        strength,
            'strength_label':  strength_label,
            'charset_size':    len(charset),
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
