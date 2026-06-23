import numpy as np

def cosine_similarity(a, b) -> float:
    """
    Computes the cosine similarity between two vectors a and b.
    """
    vec_a = np.array(a, dtype=np.float32)
    vec_b = np.array(b, dtype=np.float32)
    
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
        
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))
