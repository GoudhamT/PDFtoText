import os
from pathlib import Path
from flask import Flask,render_template , request ,redirect ,url_for,abort
import pdf2image
import pytesseract
from pytesseract import Output
from pdf2image import convert_from_path
from PIL import Image
from werkzeug.utils import secure_filename
from cfenv import AppEnv
from sap import xssec

# UPLOAD_FOLDER = 'uploadFolder/'
UPLOAD_FOLDER = 'templates/'
app = Flask(__name__)
env = AppEnv()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
port = int(os.environ.get('PORT', 3000))
uaa_service = env.get_service(name='PDFScannerPDFtoText-oauth').credentials

@app.route('/')
def UI():
    return render_template("index.html")

@app.route('/extractPDFtext', methods = ['POST'])
def scanPDFtoText():
    if request.method == 'POST':
        if 'authorization' not in request.headers:
            abort(403)

        access_token = request.headers.get('authorization')[7:]
        security_context = xssec.create_security_context(access_token, uaa_service)
        is_authorized = security_context.check_scope('uaa.resource')

        if not is_authorized:
            abort(403)

        f = request.files['file']
        if not f.filename:
            return {"message": "No upload file sent"}
        elif not f.filename.endswith(".pdf"):
            return {"message": "Only pdf file upload allowed!"}
        else:
            filename = secure_filename(f.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # return str(filepath)
            f.save(filepath)
            try:
                l = []
                image = pdf2image.convert_from_path(filepath)
                for pagenumber, page in enumerate(image):
                    detected_text = pytesseract.image_to_string(page)
                    l.append(detected_text) 
                else:
                    clean_extract = "".join(l).replace("\n", " ").strip()
                    return clean_extract
            except Exception as e:
                return str(e)
            finally:
                if os.path.isfile(filepath):
                    os.remove(filepath)
                # os.remove(filepath)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)