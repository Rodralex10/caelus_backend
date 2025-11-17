from flask import Flask, request, jsonify
import os
import uuid
import fitz  # PyMuPDF
from paddleocr import PaddleOCR
from PIL import Image

app = Flask(__name__)

# Pasta para uploads
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inicializar OCR (Português + Inglês)
ocr = PaddleOCR(lang="pt", use_angle_cls=True)

def extract_text_from_image(img):
    results = ocr.ocr(img, cls=True)
    text = ""
    for line in results:
        for part in line:
            text += part[1][0] + "\n"
    return text


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text_final = ""

    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text_final += extract_text_from_image(img)

    return text_final


def extract_info(text):
    text_lower = text.lower()

    return {
        "medicine_name": "",
        "frequency": "",
        "dosage": "",
        "until": "",
        "raw_text": text
    }


@app.route("/process", methods=["POST"])
def process():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded = request.files["file"]

    filename = f"{uuid.uuid4().hex}-{uploaded.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    uploaded.save(filepath)

    try:
        if filename.lower().endswith(".pdf"):
            text = extract_text_from_pdf(filepath)
        else:
            img = Image.open(filepath)
            text = extract_text_from_image(img)

        info = extract_info(text)

        return jsonify({
            "ok": True,
            "extracted_text": text,
            "info": info
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return "PaddleOCR API is running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
