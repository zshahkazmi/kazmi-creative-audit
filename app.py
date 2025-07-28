from flask import Flask, render_template, request
import os
from audit_tool import audit_website

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    report = None
    if request.method == 'POST':
        url = request.form.get('url')
        if url:
            report = audit_website(url)
    return render_template('index.html', report=report)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
