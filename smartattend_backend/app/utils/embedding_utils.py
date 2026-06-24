"""
SmartAttend AI — Embedding / Vector Utilities
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

    Designed for 5 000+ student scale:
    Processes the entire 50-embedding gallery of a single student in one matmul.
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


def max_cosine_similarity(
    query: Union[np.ndarray, List[float]],
    gallery: List[Union[np.ndarray, List[float]]],
) -> float:
    """
    Return the maximum cosine similarity between `query` and any
    vector in `gallery`. Returns 0.0 if gallery is empty.
    """
    sims = batch_cosine_similarities(query, gallery)
    return max(sims) if sims else 0.0
