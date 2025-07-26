from flask import Flask, render_template, request, send_file
import os
import time
from audit_tool import website_audit, generate_pdf_report

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            report = website_audit(url)
            filename = f"Kazmi_Creative_Audit_{int(time.time())}.pdf"
            filepath = os.path.join("reports", filename)
            os.makedirs("reports", exist_ok=True)
            generate_pdf_report(report, filename=filepath)
            return send_file(filepath, as_attachment=True)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
