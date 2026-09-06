# ==============================================================
# YouTube Downloader — ToolsHub Backend
# POST /api/youtube/info     → video info + format list
# POST /api/youtube/download → download via yt-dlp to temp, serve file
# ==============================================================

from flask import Blueprint, request, jsonify, send_file
import yt_dlp
import re
import os
import tempfile
import glob

youtube_bp = Blueprint('youtube', __name__)

def is_valid_url(url):
    return bool(re.search(r'(youtube\.com|youtu\.be)', url))

# Map quality label → yt-dlp format string
FORMAT_STRINGS = {
    '4K':    'bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=2160]+bestaudio/best[height<=2160]',
    '2K':    'bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1440]+bestaudio/best[height<=1440]',
    '1080p': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]',
    '720p':  'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]',
    '480p':  'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]',
    '360p':  'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=360]+bestaudio/best[height<=360]',
    '240p':  'best[height<=240]',
    '144p':  'best[height<=144]/worst',
    'M4A':   'bestaudio[ext=m4a]/bestaudio',
    'WEBM':  'bestaudio[ext=webm]/bestaudio',
    'WEBM Audio': 'bestaudio[ext=webm]/bestaudio',
    'OPUS':  'bestaudio[ext=opus]/bestaudio',
    'MP3':   'bestaudio',
}


@youtube_bp.route('/info', methods=['POST'])
def get_info():
    data = request.get_json(silent=True) or {}
    url  = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'URL daalen'}), 400
    if not is_valid_url(url):
        return jsonify({'error': 'Valid YouTube URL chahiye'}), 400

    ydl_opts = {'quiet': True, 'no_warnings': True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = []
        seen_v = set()
        seen_a = set()

        for f in (info.get('formats') or []):
            h      = f.get('height') or 0
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            ext    = f.get('ext', '')
            fsize  = f.get('filesize') or f.get('filesize_approx')

            # ── Video formats ──
            if vcodec != 'none' and h:
                if   h >= 2160: qlbl = '4K'
                elif h >= 1440: qlbl = '2K'
                elif h >= 1080: qlbl = '1080p'
                elif h >= 720:  qlbl = '720p'
                elif h >= 480:  qlbl = '480p'
                elif h >= 360:  qlbl = '360p'
                elif h >= 240:  qlbl = '240p'
                else:           qlbl = '144p'

                if qlbl not in seen_v:
                    seen_v.add(qlbl)
                    formats.append({
                        'label':    qlbl,
                        'kind':     'video',
                        'height':   h,
                        'ext':      'mp4',
                        'filesize': fsize,
                    })

            # ── Audio only formats ──
            elif acodec != 'none' and vcodec == 'none':
                albl = ext.upper()
                if ext == 'webm': albl = 'WEBM Audio'
                if albl not in seen_a:
                    seen_a.add(albl)
                    formats.append({
                        'label':    albl,
                        'kind':     'audio',
                        'height':   0,
                        'ext':      ext,
                        'filesize': fsize,
                        'abr':      f.get('abr'),
                    })

        # Sort: video (high→low) then audio
        video_fmts = sorted([f for f in formats if f['kind'] == 'video'],
                            key=lambda x: x['height'], reverse=True)
        audio_fmts = [f for f in formats if f['kind'] == 'audio']
        formats    = video_fmts + audio_fmts

        return jsonify({
            'title':      info.get('title', 'Unknown'),
            'uploader':   info.get('uploader', ''),
            'duration':   info.get('duration', 0),
            'thumbnail':  info.get('thumbnail', ''),
            'view_count': info.get('view_count', 0),
            'formats':    formats,
        })

    except yt_dlp.utils.DownloadError as e:
        return jsonify({'error': str(e)[:200]}), 400
    except Exception as e:
        return jsonify({'error': str(e)[:300]}), 500


@youtube_bp.route('/download', methods=['POST'])
def download_video():
    """
    Downloads via yt-dlp to temp file, then serves it.
    Uses video ID as filename to avoid Windows invalid character errors.
    """
    data     = request.get_json(silent=True) or {}
    url      = data.get('url', '').strip()
    quality  = data.get('quality', '720p')

    if not url:
        return jsonify({'error': 'URL daalen'}), 400
    if not is_valid_url(url):
        return jsonify({'error': 'Valid YouTube URL chahiye'}), 400

    fmt_str = FORMAT_STRINGS.get(quality, 'bestvideo+bestaudio/best')

    tmpdir = tempfile.mkdtemp()
    try:
        # Use video ID as filename — avoids Windows invalid char errors
        out_template = os.path.join(tmpdir, '%(id)s.%(ext)s')

        ydl_opts = {
            'quiet':                True,
            'no_warnings':          True,
            'format':               fmt_str,
            'outtmpl':              out_template,
            'noplaylist':           True,
            'merge_output_format':  'mp4',
            'windowsfilenames':     True,   # yt-dlp built-in Windows safe names
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            vid_id = info.get('id', 'video')
            title  = info.get('title', 'video')

        # Find the downloaded file by video ID prefix
        files = glob.glob(os.path.join(tmpdir, f'{vid_id}.*'))
        if not files:
            files = glob.glob(os.path.join(tmpdir, '*'))
        if not files:
            return jsonify({'error': 'File download nahi hua — try karo dobara'}), 500

        out_path = files[0]
        ext      = os.path.splitext(out_path)[1].lstrip('.')

        # Build safe download name for browser
        safe_title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', title).strip()[:60] or 'video'
        dl_name    = f"{safe_title}.{ext}"

        mime_map = {
            'mp4': 'video/mp4', 'webm': 'video/webm', 'mkv': 'video/x-matroska',
            'm4a': 'audio/mp4', 'mp3': 'audio/mpeg', 'ogg': 'audio/ogg',
            'opus': 'audio/ogg', 'aac': 'audio/aac',
        }
        mime = mime_map.get(ext, 'application/octet-stream')

        return send_file(
            out_path,
            as_attachment=True,
            download_name=dl_name,
            mimetype=mime,
        )

    except yt_dlp.utils.DownloadError as e:
        err = str(e)
        if 'Sign in' in err or 'login' in err.lower():
            return jsonify({'error': 'Yeh video age-restricted ya private hai'}), 400
        return jsonify({'error': err[:300]}), 400
    except Exception as e:
        return jsonify({'error': str(e)[:300]}), 500

