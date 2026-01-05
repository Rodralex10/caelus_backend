FROM paddlepaddle/paddle:2.6.2  # CPU base with Paddle libs

RUN apt-get update && \
    apt-get install -y poppler-utils libgl1 libglib2.0-0 libheif1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=10000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
