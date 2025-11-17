from flask import Flask, request, jsonify
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def extract_info(text):
    text = text.lower()

    name = ""
    freq = ""
    dosage = ""
    until = ""

    for line in text.split("\n"):
        if "mg" in line or "ml" in line:
            dosage = line.strip()

        if "de" in line and "em" in line:
            freq = line.strip()

        if "até" in line or "durante" in line:
            until = line.strip()

        if any(word in line for word in ["dol", "ben-u-ron", "aspirina", "ibuprof", "paracet"]):
            name = line.strip()

    return {
        "medicine_name": name,
        "dosage": dosage,
        "frequency": freq,
        "until_when": until,
    }


@app.route("/process", methods=["POST"])
def process_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    filename = f"{uuid.uuid4().hex}-{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    extracted_text = ""

    try:
        if filename.lower().endswith(".pdf"):
            images = convert_from_path(filepath, dpi=200)

            for img in images:
                extracted_text += "\n" + pytesseract.image_to_string(img)

        else:
            img = Image.open(filepath)
            extracted_text = pytesseract.image_to_string(img)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    info = extract_info(extracted_text)

    return jsonify({
        "raw_text": extracted_text,
        "extracted": info
    })


@app.route("/", methods=["GET"])
def home():
    return "Caelus OCR API is running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)