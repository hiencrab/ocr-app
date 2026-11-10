FROM python:3.11-slim

WORKDIR /app

# Cài poppler và các lib hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Cài PaddlePaddle CPU trước (tránh conflict)
RUN pip install --no-cache-dir paddlepaddle==3.0.0

# Cài PaddleOCR và Flask
RUN pip install --no-cache-dir \
    paddleocr==2.9.1 \
    flask==3.1.0 \
    pdf2image==1.17.0 \
    Pillow \
    langdetect

# Copy code vào container
COPY app.py ocr_engine.py ./
COPY templates/ ./templates/

# Tạo thư mục uploads
RUN mkdir -p uploads

EXPOSE 5000

CMD ["python", "app.py"]
