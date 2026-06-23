import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from typing import List, Dict, Any
from app.utils.embedding_utils import cosine_similarity

_face_app = None

def get_face_analysis_app() -> FaceAnalysis:
    """
    Lazy initializer for InsightFace FaceAnalysis to prevent loading
    during Alembic migrations or unit test setups.
    """
    global _face_app
    if _face_app is None:
        # Use CPUExecutionProvider for standard Render or local environments without GPUs
        _face_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        _face_app.prepare(ctx_id=0, det_size=(640, 640))
    return _face_app

def get_embedding(image_bytes: bytes) -> np.ndarray:
    """
    Decodes image from bytes, detects the face, and returns its 512-dim ArcFace embedding.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Failed to decode image bytes")
        
    app = get_face_analysis_app()
    faces = app.get(img)
    if not faces:
        raise ValueError("No face detected in image")
        
    # faces[0].normed_embedding is a 512-dim float32 vector
    return faces[0].normed_embedding

def get_sharpness(image_bytes: bytes) -> float:
    """
    Calculates image sharpness using the variance of the Laplacian.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return 0.0
    return float(cv2.Laplacian(img, cv2.CV_64F).var())

def select_best_embeddings(frames: List[bytes], target: int = 50) -> List[np.ndarray]:
    """
    Filters and selects the best face embeddings out of a list of frame bytes.
    Ensures high confidence, sharpness > 100, and cosine similarity < 0.98.
    """
    candidates = []
    app = get_face_analysis_app()
    
    for frame_bytes in frames:
        try:
            # First verify sharpness to quickly skip blurred frames before running inference
            sharpness = get_sharpness(frame_bytes)
            if sharpness <= 100.0:
                continue
                
            nparr = np.frombuffer(frame_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                continue
                
            faces = app.get(img)
            if not faces:
                continue
                
            face = faces[0]
            # Face detection confidence > 0.95
            if face.det_score < 0.95:
                continue
                
            candidates.append({
                'embedding': face.normed_embedding,
                'sharpness': sharpness
            })
        except Exception:
            continue
            
    # Sort candidates by sharpness in descending order
    candidates.sort(key=lambda x: x['sharpness'], reverse=True)
    
    kept = []
    for c in candidates:
        if len(kept) >= target:
            break
        # Keep only if cosine similarity is < 0.98 with all already kept
        if all(cosine_similarity(c['embedding'], k['embedding']) < 0.98 for k in kept):
            kept.append(c)
            
    return [k['embedding'] for k in kept]
