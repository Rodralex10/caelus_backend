import os
import tempfile
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from paddleocr import PaddleOCRVL
from pdf2image import convert_from_bytes
from pillow_heif import register_heif_opener

register_heif_opener()

app = FastAPI(title="Prescription OCR API")

pipeline = PaddleOCRVL()  # default init

SUPPORTED_IMAGE_TYPES = {
    "image/jpeg", "image/png", "image/heic", "image/heif",
    "image/webp", "image/tiff",
}
SUPPORTED_PDF_TYPES = {"application/pdf"}
SUPPORTED_TYPES = SUPPORTED_IMAGE_TYPES | SUPPORTED_PDF_TYPES


def ocr_image(path: str) -> str:
    out = pipeline.predict(path)
    texts = []
    for res in out:
        if hasattr(res, "text"):
            texts.append(res.text)
        elif isinstance(res, dict) and "text" in res:
            texts.append(res["text"])
    return "\n".join(texts).strip()


def process_pdf(data: bytes) -> tuple[str, int]:
    pages = convert_from_bytes(data, dpi=300)  # PDF -> images
    tmpdir = tempfile.mkdtemp(prefix="pdf_vl_")
    texts = []
    try:
        for i, img in enumerate(pages, 1):
            p = os.path.join(tmpdir, f"page_{i}.png")
            img.save(p, "PNG")
            texts.append(ocr_image(p))
        return "\n\n".join(texts).strip(), len(pages)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def process_image(data: bytes) -> tuple[str, int]:
    tmpdir = tempfile.mkdtemp(prefix="img_vl_")
    p = os.path.join(tmpdir, "upload.png")
    try:
        with open(p, "wb") as f:
            f.write(data)
        return ocr_image(p), 1
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def extract_medicine_name(text: str) -> str:
    candidates = [ln.strip() for ln in text.splitlines() if len(ln.strip()) > 3]
    for ln in candidates:
        alpha = sum(c.isalpha() for c in ln)
        if alpha >= 4 and alpha / max(1, len(ln)) > 0.5:
            return ln
    return candidates[0] if candidates else ""


@app.post("/prescription/scan")
async def scan_prescription(file: UploadFile = File(...)):
    if file.content_type not in SUPPORTED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
    data = await file.read()
    try:
        if file.content_type in SUPPORTED_PDF_TYPES:
            texto, pages = process_pdf(data)
        else:
            texto, pages = process_image(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to process file.") from e

    med_name = extract_medicine_name(texto)
    return JSONResponse({"texto": texto, "paginas": pages, "medicamento": med_name})
