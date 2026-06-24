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

# ── Pre-cache AI models during build (avoids runtime downloads on Render) ─────
# buffalo_l ArcFace model (~670 MB) — downloads from InsightFace CDN
RUN python -c "\
from insightface.app import FaceAnalysis; \
app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider']); \
app.prepare(ctx_id=0, det_size=(640, 640)); \
print('[Docker] ArcFace buffalo_l model cached successfully.')" || \
    echo "[Docker] WARNING: ArcFace model pre-cache failed. Will download at runtime."

# DeepFace Emotion model (~50 MB)
RUN python -c "\
from deepface import DeepFace; \
DeepFace.build_model('Emotion'); \
print('[Docker] DeepFace Emotion model cached successfully.')" || \
    echo "[Docker] WARNING: DeepFace model pre-cache failed. Will download at runtime."

# ── Application code ──────────────────────────────────────────────────────────
COPY . .

# ── Startup ───────────────────────────────────────────────────────────────────
# Render provides $PORT automatically
CMD uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2 --timeout-keep-alive 65
