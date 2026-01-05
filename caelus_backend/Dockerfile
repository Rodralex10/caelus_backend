FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y poppler-utils libgl1 libglib2.0-0 libheif1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download PaddleOCR-VL weights at build time (avoids first-request timeout)
ENV HF_HOME=/app/hf_models
RUN python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="PaddlePaddle/PaddleOCR-VL",
    local_dir="/app/hf_models/paddleocr_vl",
    local_dir_use_symlinks=False
)
PY

COPY app ./app
ENV PORT=10000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
