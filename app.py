import os
import tempfile

from flask import Flask, after_this_request, render_template, request, send_file

from audit_tool import audit_website

try:
    import yt_dlp
except ImportError:  # pragma: no cover - fallback if optional dependency missing
    yt_dlp = None

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

@app.route('/', methods=['GET', 'POST'])
def index():
    report = None
    if request.method == 'POST':
        url = request.form.get('url')
        if url:
            report = audit_website(url)
    return render_template('index.html', report=report)


@app.route('/youtube-downloader', methods=['GET', 'POST'])
def youtube_downloader():
    error = None

    if request.method == 'POST':
        video_url = (request.form.get('video_url') or '').strip()

        if not video_url:
            error = "Please provide a YouTube video URL."
        elif yt_dlp is None:
            error = "The yt-dlp package is not installed on the server."
        else:
            temp_dir = tempfile.mkdtemp(prefix='yt-dlp-')
            ydl_opts = {
                'format': 'bv*+ba/best',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'restrictfilenames': True,
                'noplaylist': True,
                'quiet': True,
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=True)
                    file_path = ydl.prepare_filename(info)

                filename = os.path.basename(file_path)

                @after_this_request
                def cleanup(response):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass
                    try:
                        os.rmdir(temp_dir)
                    except OSError:
                        pass
                    return response

                return send_file(file_path, as_attachment=True, download_name=filename)
            except Exception as exc:  # pragma: no cover - network/IO errors
                error = f"Unable to download the requested video: {exc}"

    return render_template('youtube.html', error=error)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
