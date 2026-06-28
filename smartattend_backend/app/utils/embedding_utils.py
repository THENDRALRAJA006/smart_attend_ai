"""
SmartAttend AI — Embedding / Vector Utilities

Provides cosine similarity computations and master embedding generation
for the ArcFace-based biometric verification system.
"""
import numpy as np
from typing import List, Union


def cosine_similarity(
    a: Union[np.ndarray, List[float]],
    b: Union[np.ndarray, List[float]],
) -> float:
    """
    Compute cosine similarity between two vectors.

    Returns a value in [-1, 1] where 1 means identical direction.
    Uses float32 for efficiency on large embedding matrices.
    """
    vec_a = np.array(a, dtype=np.float32)
    vec_b = np.array(b, dtype=np.float32)

    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def batch_cosine_similarities(
    query: Union[np.ndarray, List[float]],
    gallery: List[Union[np.ndarray, List[float]]],
) -> List[float]:
    """
    Efficiently compute cosine similarity of `query` against all vectors
    in `gallery` using vectorised numpy operations.

    Used internally by the outlier detection pipeline.
    """
    if not gallery:
        return []

    q = np.array(query, dtype=np.float32)
    g = np.array(gallery, dtype=np.float32)  # shape: (N, 512)

    # Normalise query
    q_norm = np.linalg.norm(q)
    if q_norm == 0.0:
        return [0.0] * len(gallery)
    q_unit = q / q_norm

    # Normalise gallery rows
    g_norms = np.linalg.norm(g, axis=1, keepdims=True)
    g_norms = np.where(g_norms == 0, 1.0, g_norms)  # Avoid division by zero
    g_unit = g / g_norms

    # Batch dot product
    similarities = g_unit @ q_unit  # shape: (N,)
    return similarities.tolist()


def compute_master_embedding(
    embeddings: List[np.ndarray],
) -> np.ndarray:
    """
    Compute a single master embedding as the L2-normalised mean of
    all input embeddings.

    This is the standard approach used in production biometric systems
    (FaceNet, ArcFace papers). The mean of L2-normalised embeddings
    represents the centroid of the face's identity cluster in the
    512-dimensional embedding space.

    Args:
        embeddings: List of 512-dim normalised ArcFace embeddings.

    Returns:
        L2-normalised 512-dim master embedding.
    """
    stacked = np.array(embeddings, dtype=np.float32)  # (N, 512)
    mean_emb = stacked.mean(axis=0)  # (512,)

    norm = np.linalg.norm(mean_emb)
    if norm > 0:
        mean_emb = mean_emb / norm

    return mean_emb
