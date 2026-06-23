FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Install system runtime dependencies:
# - build-essential and libpq-dev for compiling PostgreSQL client drivers.
# - libgl1 and libglib2.0-0 to support OpenCV (instead of deprecated libgl1-mesa-glx).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to utilize Docker build layer caching
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-cache InsightFace (buffalo_l) and DeepFace (Emotion) model weights during build.
# This prevents runtime network download overhead and makes deployment self-sufficient on Render.
RUN python -c "from insightface.app import FaceAnalysis; FaceAnalysis(name='buffalo_l')" || true
RUN python -c "from deepface import DeepFace; DeepFace.build_model('Emotion')" || true

# Copy all project source code
COPY . .

# Run the FastAPI server using uvicorn on the configured port
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
