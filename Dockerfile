FROM python:3.10-slim

# === Environment Variables ===
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV EMBED_MODEL=/app/embed_model
ENV DATA_ENG=/app/static/data/legal_english
ENV DATA_JAP=/app/static/data/legal_japanese
ENV STATIC_PATH=/app/static
ENV HF_HOME=/app/embed_model/.cache

WORKDIR /app

# === Install OS dependencies ===
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    netcat-traditional \
    libgl1-mesa-glx \
    nginx \
    certbot \
    python3-certbot-nginx \
    && rm -rf /var/lib/apt/lists/*

# === Python dependencies ===
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# === Copy app code ===
COPY . .

# === Create required directories ===
RUN mkdir -p \
    /app/static/data/legal_english \
    /app/static/data/legal_japanese \
    /app/embed_model/.cache && \
    chmod -R 777 /app

# === Copy Nginx config ===
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# === Expose ports ===
EXPOSE 80 443