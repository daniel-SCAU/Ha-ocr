FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements_ocr.txt /app/requirements_ocr.txt
RUN pip install --no-cache-dir -r /app/requirements_ocr.txt

COPY ocr_app /app/ocr_app

EXPOSE 8080

CMD ["python", "-m", "ocr_app.server"]
