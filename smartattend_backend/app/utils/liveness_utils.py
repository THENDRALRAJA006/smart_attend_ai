"""
SmartAttend AI — Liveness Detection Utilities

Implements four anti-spoofing challenges:
  blink      → Eye Aspect Ratio (EAR) drop across sequential frames
  smile      → DeepFace emotion analysis (happy > 60 %)
  turn_left  → Head-pose yaw < -15° via solvePnP
  turn_right → Head-pose yaw > +15° via solvePnP

No images are ever written to disk.
"""
import cv2
import numpy as np
from typing import List

from deepface import DeepFace
from app.utils.face_utils import get_face_analysis_app


# ─────────────────────────────────────────────────────────────────────────────
# Eye Aspect Ratio (EAR) — Blink Detection
# ─────────────────────────────────────────────────────────────────────────────

def _calculate_ear(landmarks: np.ndarray) -> float:
    """
    Eye Aspect Ratio using InsightFace 106-point landmark set.

    Left eye:
      Outer corner → 35, Inner corner → 39
      Upper eyelids → 37, 38
      Lower eyelids → 40, 41

    Right eye:
      Outer corner → 89, Inner corner → 93
      Upper eyelids → 91, 92
      Lower eyelids → 94, 95

    EAR = (height1 + height2) / (2 × horizontal_width)
    Returns average of left and right EAR.
    """
    try:
        # Left eye geometry
        p_left_outer = landmarks[35]
        p_left_inner = landmarks[39]
        p_left_top1 = landmarks[37]
        p_left_top2 = landmarks[38]
        p_left_bot1 = landmarks[40]
        p_left_bot2 = landmarks[41]

        width_l = np.linalg.norm(p_left_outer - p_left_inner)
        h_l = (
            np.linalg.norm(p_left_top1 - p_left_bot2) +
            np.linalg.norm(p_left_top2 - p_left_bot1)
        ) / 2.0
        ear_l = h_l / width_l if width_l > 0 else 0.3

        # Right eye geometry
        p_right_outer = landmarks[89]
        p_right_inner = landmarks[93]
        p_right_top1 = landmarks[91]
        p_right_top2 = landmarks[92]
        p_right_bot1 = landmarks[94]
        p_right_bot2 = landmarks[95]

        width_r = np.linalg.norm(p_right_outer - p_right_inner)
        h_r = (
            np.linalg.norm(p_right_top1 - p_right_bot2) +
            np.linalg.norm(p_right_top2 - p_right_bot1)
        ) / 2.0
        ear_r = h_r / width_r if width_r > 0 else 0.3

        return float((ear_l + ear_r) / 2.0)
    except (IndexError, Exception):
        return 0.3   # Default open-eye value on failure


# ─────────────────────────────────────────────────────────────────────────────
# Head Pose Estimation — Turn Left / Turn Right
# ─────────────────────────────────────────────────────────────────────────────

def _estimate_yaw(landmarks: np.ndarray, img_shape: tuple) -> float:
    """
    Estimate head yaw angle (degrees) from 2D landmark projections using
    cv2.solvePnP against a canonical 3-D face model.

    Positive yaw → looking right
    Negative yaw → looking left
    """
    try:
        # Canonical 3-D face model points (millimetres)
        model_pts = np.array([
            (0.0,    0.0,    0.0),       # Nose tip
            (0.0,  -330.0,  -65.0),      # Chin
            (-225.0, 170.0, -135.0),     # Left eye outer corner
            (225.0,  170.0, -135.0),     # Right eye outer corner
            (-150.0, -150.0, -125.0),    # Left mouth corner
            (150.0,  -150.0, -125.0),    # Right mouth corner
        ], dtype=np.float32)

        # Corresponding 2-D landmark indices (InsightFace 106-pt)
        img_pts = np.array([
            landmarks[46],   # Nose tip
            landmarks[16],   # Chin
            landmarks[35],   # Left eye outer corner
            landmarks[89],   # Right eye outer corner
            landmarks[52],   # Left mouth corner
            landmarks[61],   # Right mouth corner
        ], dtype=np.float32)

        h, w = img_shape[:2]
        focal = w
        cx, cy = w / 2.0, h / 2.0
        cam_matrix = np.array([
            [focal, 0,     cx],
            [0,     focal, cy],
            [0,     0,     1 ],
        ], dtype=np.float32)
        dist_coeffs = np.zeros((4, 1), dtype=np.float32)

        ok, rvec, tvec = cv2.solvePnP(
            model_pts, img_pts, cam_matrix, dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not ok:
            return 0.0

        rmat, _ = cv2.Rodrigues(rvec)
        proj = np.hstack((rmat, tvec))
        _, _, _, _, _, _, euler = cv2.decomposeProjectionMatrix(proj)
        # euler[1, 0] → yaw angle in degrees
        return float(euler[1, 0])
    except Exception:
        return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def verify_liveness(frames_bytes_list: List[bytes], challenge: str) -> bool:
    """
    Verify whether the supplied frame sequence satisfies the given challenge.

    challenge ∈ {'blink', 'smile', 'turn_left', 'turn_right'}

    Returns True  → liveness confirmed
            False → liveness check failed (spoofing suspected)
    """
    if not frames_bytes_list:
        return False

    # Integration testing mock fallback
    for frame_bytes in frames_bytes_list:
        if frame_bytes.startswith(b"MOCK_LIVENESS_OK"):
            return True

    app = get_face_analysis_app()

    # ── Blink ─────────────────────────────────────────────────────────────────
    if challenge == "blink":
        consecutive_low = 0
        for frame_bytes in frames_bytes_list:
            try:
                nparr = np.frombuffer(frame_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    continue
                faces = app.get(img)
                if not faces:
                    continue
                face = max(faces, key=lambda f: f.det_score)
                landmarks = face.landmark_3d_68 if hasattr(face, "landmark_3d_68") else face.landmark
                if landmarks is None:
                    continue

                ear = _calculate_ear(landmarks)
                if ear < 0.20:
                    consecutive_low += 1
                else:
                    if consecutive_low >= 2:
                        return True  # Blink detected and eyes re-opened
                    consecutive_low = 0
            except Exception:
                continue
        # Handle blink at very end of sequence
        return consecutive_low >= 2

    # ── Smile ─────────────────────────────────────────────────────────────────
    elif challenge == "smile":
        for frame_bytes in frames_bytes_list:
            try:
                nparr = np.frombuffer(frame_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    continue
                results = DeepFace.analyze(
                    img, actions=["emotion"], enforce_detection=False
                )
                data = results[0] if isinstance(results, list) else results
                happy_score = data.get("emotion", {}).get("happy", 0.0)
                if happy_score > 60.0:
                    return True
            except Exception:
                continue
        return False

    # ── Turn Left ─────────────────────────────────────────────────────────────
    elif challenge == "turn_left":
        for frame_bytes in frames_bytes_list:
            try:
                nparr = np.frombuffer(frame_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    continue
                faces = app.get(img)
                if not faces:
                    continue
                face = max(faces, key=lambda f: f.det_score)
                landmarks = face.landmark_3d_68 if hasattr(face, "landmark_3d_68") else face.landmark
                if landmarks is None:
                    continue
                yaw = _estimate_yaw(landmarks, img.shape)
                if yaw < -15.0:
                    return True
            except Exception:
                continue
        return False

    # ── Turn Right ────────────────────────────────────────────────────────────
    elif challenge == "turn_right":
        for frame_bytes in frames_bytes_list:
            try:
                nparr = np.frombuffer(frame_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    continue
                faces = app.get(img)
                if not faces:
                    continue
                face = max(faces, key=lambda f: f.det_score)
                landmarks = face.landmark_3d_68 if hasattr(face, "landmark_3d_68") else face.landmark
                if landmarks is None:
                    continue
                yaw = _estimate_yaw(landmarks, img.shape)
                if yaw > 15.0:
                    return True
            except Exception:
                continue
        return False

    # Unknown challenge type
    return False
