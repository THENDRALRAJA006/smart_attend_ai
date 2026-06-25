FROM python:3.11-slim

# ── Environment ───────────────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# ── System dependencies ───────────────────────────────────────────────────────
# libgl1 + libglib2.0-0   → OpenCV
# default-libmysqlclient-dev → PyMySQL native support
# build-essential          → compile native extension wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Application code ──────────────────────────────────────────────────────────
COPY . .

# ── Startup ───────────────────────────────────────────────────────────────────
# Render provides $PORT automatically
CMD gunicorn main:app -k uvicorn.workers.UvicornWorker --workers 1 --threads 1 --timeout 120 --bind 0.0.0.0:$PORT

