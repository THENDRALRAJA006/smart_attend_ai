"""
SmartAttend AI — ArcFace Embedding Utilities

Uses InsightFace buffalo_s model (512-dim normed_embedding).
All processing is in-memory — no images ever written to disk.

Core functions used by both EmbeddingService (registration) and
attendance verification endpoints.
"""
import cv2
import numpy as np
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from insightface.app import FaceAnalysis

from app.config.config import settings

# ── Lazy-loaded singleton ─────────────────────────────────────────────────────
_face_app: Optional["FaceAnalysis"] = None


def get_face_analysis_app() -> Any:
    """
    Lazy-initialises the InsightFace FaceAnalysis app so that Alembic
    migrations and test imports do NOT trigger model loading.
    """
    global _face_app
    if _face_app is None:
        import sys
        import io
        
        # Temporarily redirect stdout to suppress verbose insightface/onnxruntime startup logs
        original_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            from insightface.app import FaceAnalysis
            _face_app = FaceAnalysis(
                name=settings.ARCFACE_MODEL_NAME,
                providers=["CPUExecutionProvider"],
            )
            _face_app.prepare(ctx_id=-1, det_size=(640, 640))
        finally:
            # Always restore stdout
            sys.stdout = original_stdout
    return _face_app



# ── Core Embedding Extraction ─────────────────────────────────────────────────

def get_embedding(image_bytes: bytes) -> np.ndarray:
    """
    Decode image from raw bytes, detect the largest face, and return
    the 512-dim ArcFace normed_embedding.

    Used by attendance verification to extract the live selfie embedding.

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

    # Free image buffer immediately after face detection
    del img

    if not faces:
        raise ValueError("No face detected in the supplied image")

    # Pick highest-confidence face
    best_face = max(faces, key=lambda f: f.det_score)
    embedding = best_face.normed_embedding  # 512-dim float32 ndarray

    del faces
    return embedding


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
    sharpness = float(cv2.Laplacian(img, cv2.CV_64F).var())
    del img
    return sharpness
