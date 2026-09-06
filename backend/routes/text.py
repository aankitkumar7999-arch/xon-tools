# ==============================================================
# Text Tools Route
# POST /api/text/analyze  → { text } → stats
# POST /api/text/convert  → { text, mode } → converted text
# ==============================================================

from flask import Blueprint, request, jsonify
import re

text_bp = Blueprint('text', __name__)

@text_bp.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    text = (data or {}).get('text', '')

    if not text:
        return jsonify({'error': 'Text provide karein'}), 400

    words      = text.split()
    sentences  = re.split(r'[.!?]+', text)
    sentences  = [s.strip() for s in sentences if s.strip()]
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    # Reading time (avg 200 words/min)
    reading_time_sec = round(len(words) / 200 * 60)

    return jsonify({
        'char_count':       len(text),
        'char_no_spaces':   len(text.replace(' ', '')),
        'word_count':       len(words),
        'sentence_count':   len(sentences),
        'paragraph_count':  len(paragraphs),
        'line_count':       len(text.splitlines()),
        'reading_time_sec': reading_time_sec,
        'unique_words':     len(set(w.lower().strip('.,!?') for w in words)),
        'avg_word_length':  round(sum(len(w) for w in words) / max(len(words), 1), 2),
    })


@text_bp.route('/convert', methods=['POST'])
def convert():
    data = request.get_json()
    text = (data or {}).get('text', '')
    mode = (data or {}).get('mode', 'upper')

    if not text:
        return jsonify({'error': 'Text provide karein'}), 400

    modes = {
        'upper':      text.upper(),
        'lower':      text.lower(),
        'title':      text.title(),
        'sentence':   text.capitalize(),
        'reverse':    text[::-1],
        'slug':       re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-'),
        'no_spaces':  text.replace(' ', ''),
        'trim':       '\n'.join(line.strip() for line in text.splitlines()),
        'no_dupes':   '\n'.join(dict.fromkeys(text.splitlines())),
    }

    result = modes.get(mode)
    if result is None:
        return jsonify({'error': f'Invalid mode: {mode}'}), 400

    return jsonify({'result': result, 'mode': mode})
