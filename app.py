import os
from pathlib import Path

from flask import Flask, redirect, render_template, request, send_file, url_for

from audit_tool import audit_website, generate_pdf_report

app = Flask(__name__)

REPORTS_DIR = Path(__file__).resolve().parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    report = None
    pdf_filename = None
    error = None
    if request.method == 'POST':
        url = (request.form.get('url') or '').strip()
        if url:
            try:
                report = audit_website(url)
                pdf_path = generate_pdf_report(report, output_dir=str(REPORTS_DIR))
                pdf_filename = Path(pdf_path).name
            except Exception:
                error = 'An error occurred while generating the audit. Please try again.'
        else:
            error = 'Please enter a valid URL.'
    return render_template('index.html', report=report, pdf_filename=pdf_filename, error=error)


@app.route('/download/<path:filename>')
def download_report(filename):
    file_path = REPORTS_DIR / filename
    if not file_path.exists():
        return redirect(url_for('index'))
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
