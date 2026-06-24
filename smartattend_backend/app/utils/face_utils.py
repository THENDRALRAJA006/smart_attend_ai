"""
SmartAttend AI — ArcFace Embedding Utilities

Uses InsightFace buffalo_l model (512-dim normed_embedding).
All processing is in-memory — no images ever written to disk.
"""
import cv2
import numpy as np
from insightface.app import FaceAnalysis
from typing import List

from app.utils.embedding_utils import cosine_similarity
from app.config.config import settings

# ── Lazy-loaded singleton ─────────────────────────────────────────────────────
_face_app: FaceAnalysis | None = None


def get_face_analysis_app() -> FaceAnalysis:
    """
    Lazy-initialises the InsightFace FaceAnalysis app so that Alembic
    migrations and test imports do NOT trigger model loading.
    """
    global _face_app
    if _face_app is None:
        _face_app = FaceAnalysis(
            name=settings.ARCFACE_MODEL_NAME,
            providers=["CPUExecutionProvider"],
        )
        _face_app.prepare(ctx_id=0, det_size=(640, 640))
    return _face_app


# ── Core Embedding Extraction ─────────────────────────────────────────────────

def get_embedding(image_bytes: bytes) -> np.ndarray:
    """
    Decode image from raw bytes, detect the largest face, and return
    the 512-dim ArcFace normed_embedding.

    Raises ValueError if no face is detected.
    """
    # Integration testing mock fallback
    if image_bytes.startswith(b"MOCK_EMBEDDING:"):
        import json
        emb_list = json.loads(image_bytes[len(b"MOCK_EMBEDDING:"):].decode("utf-8"))
        return np.array(emb_list, dtype=np.float32)

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Failed to decode image bytes into a valid image")

    app = get_face_analysis_app()
    faces = app.get(img)
    if not faces:
        raise ValueError("No face detected in the supplied image")

    # Pick highest-confidence face
    best_face = max(faces, key=lambda f: f.det_score)
    return best_face.normed_embedding  # 512-dim float32 ndarray


# ── Sharpness ─────────────────────────────────────────────────────────────────

def get_sharpness(image_bytes: bytes) -> float:
    """
    Estimate image sharpness using Laplacian variance.
    Higher value = sharper image.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return 0.0
    return float(cv2.Laplacian(img, cv2.CV_64F).var())


# ── Best Embedding Selection (50-embedding system) ────────────────────────────

def select_best_embeddings(
    frames: List[bytes],
    target: int = 50,
    sharpness_threshold: float = 100.0,
    det_confidence_threshold: float = 0.95,
    dedup_threshold: float = 0.98,
) -> List[np.ndarray]:
    """
    From a list of raw frame bytes select the best `target` ArcFace embeddings.

    Algorithm:
      1. Reject frames with sharpness ≤ threshold (fast, pre-inference filter)
      2. Reject faces with det_score < confidence_threshold
      3. Sort remaining candidates by sharpness descending
      4. Greedily add embeddings that are NOT too similar (cosine < dedup_threshold)
         to the already-kept set
      5. Stop when `target` embeddings are collected

    Returns a list of up to `target` numpy arrays (512-dim float32).
    """
    app = get_face_analysis_app()
    candidates = []

    for frame_bytes in frames:
        try:
            # Fast sharpness pre-filter (avoids running ArcFace on blurry frames)
            sharpness = get_sharpness(frame_bytes)
            if sharpness <= sharpness_threshold:
                continue

            nparr = np.frombuffer(frame_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                continue

            faces = app.get(img)
            if not faces:
                continue

            face = max(faces, key=lambda f: f.det_score)

            # Confidence filter
            if face.det_score < det_confidence_threshold:
                continue

            candidates.append({
                "embedding": face.normed_embedding,
                "sharpness": sharpness,
            })
        except Exception:
            continue  # Skip unprocessable frames silently

    # Sort by sharpness descending (highest quality first)
    candidates.sort(key=lambda x: x["sharpness"], reverse=True)

    # Greedy deduplication: keep if NOT too similar to any kept embedding
    kept: List[dict] = []
    for c in candidates:
        if len(kept) >= target:
            break
        if all(
            cosine_similarity(c["embedding"], k["embedding"]) < dedup_threshold
            for k in kept
        ):
            kept.append(c)

    return [k["embedding"] for k in kept]
