from flask import Flask, request, jsonify
import easyocr
from PIL import Image
import uuid
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inicializar o EasyOCR (português + inglês)
reader = easyocr.Reader(["pt", "en"], gpu=False)

def extract_info(text):
    text = text.lower()
    name = ""
    freq = ""
    dosage = ""
    until = ""

    for line in text.split("\n"):
        line = line.strip()

        if "mg" in line or "ml" in line:
            dosage = line

        if "de" in line and "em" in line:
            freq = line

        if "até" in line or "durante" in line:
            until = line

        if any(med in line for med in [
            "adol", "ben-u-ron", "aspirina", "ibuprof", "paracet"
        ]):
            name = line

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

    try:
        img = Image.open(filepath).convert("RGB")

        # EasyOCR → texto
        result = reader.readtext(filepath, detail=0)
        extracted_text = "\n".join(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    info = extract_info(extracted_text)

    return jsonify({
        "raw_text": extracted_text,
        "extracted": info
    })

@app.route("/", methods=["GET"])
def home():
    return "Caelus OCR API with EasyOCR is running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
