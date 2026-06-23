import cv2
import numpy as np
from typing import List
from deepface import DeepFace
from app.utils.face_utils import get_face_analysis_app

def calculate_ear(landmarks: np.ndarray) -> float:
    """
    Calculates the Eye Aspect Ratio (EAR) from the 106 facial landmark coordinates.
    Left Eye: Outer corner (35), Inner corner (39), Upper eyelids (37, 38), Lower eyelids (40, 41)
    Right Eye: Outer corner (89), Inner corner (93), Upper eyelids (91, 92), Lower eyelids (94, 95)
    """
    try:
        # Left eye points
        p35 = landmarks[35]
        p39 = landmarks[39]
        p37 = landmarks[37]
        p38 = landmarks[38]
        p40 = landmarks[40]
        p41 = landmarks[41]
        
        # Right eye points
        p89 = landmarks[89]
        p93 = landmarks[93]
        p91 = landmarks[91]
        p92 = landmarks[92]
        p94 = landmarks[94]
        p95 = landmarks[95]
        
        # Horizontal distances
        width_l = np.linalg.norm(p35 - p39)
        width_r = np.linalg.norm(p89 - p93)
        
        # Vertical distances
        height_l1 = np.linalg.norm(p37 - p41)
        height_l2 = np.linalg.norm(p38 - p40)
        height_l = (height_l1 + height_l2) / 2.0
        
        height_r1 = np.linalg.norm(p91 - p95)
        height_r2 = np.linalg.norm(p92 - p94)
        height_r = (height_r1 + height_r2) / 2.0
        
        ear_left = height_l / width_l if width_l > 0 else 0.0
        ear_right = height_r / width_r if width_r > 0 else 0.0
        
        # Return average EAR
        return float((ear_left + ear_right) / 2.0)
    except Exception:
        return 0.3  # Default open-eye value if calculation fails

def estimate_head_pose(landmarks: np.ndarray, img_shape: tuple) -> float:
    """
    Estimates the yaw angle of the head in degrees using cv2.solvePnP.
    Positive yaw represents turning right, negative represents turning left.
    """
    try:
        # Standard 3D model points of a human face
        model_points = np.array([
            (0.0, 0.0, 0.0),             # Nose tip
            (0.0, -330.0, -65.0),        # Chin
            (-225.0, 170.0, -135.0),     # Left eye outer corner
            (225.0, 170.0, -135.0),      # Right eye outer corner
            (-150.0, -150.0, -125.0),    # Left mouth corner
            (150.0, -150.0, -125.0)      # Right mouth corner
        ], dtype=np.float32)
        
        # Corresponding 2D points from our 106-point landmark system
        image_points = np.array([
            landmarks[46],  # Nose tip
            landmarks[16],  # Chin
            landmarks[35],  # Left eye outer corner
            landmarks[89],  # Right eye outer corner
            landmarks[52],  # Left mouth corner
            landmarks[61]   # Right mouth corner
        ], dtype=np.float32)
        
        height, width = img_shape[:2]
        focal_length = width
        center = (width / 2.0, height / 2.0)
        
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype=np.float32)
        
        dist_coeffs = np.zeros((4, 1), dtype=np.float32)
        
        success, rotation_vector, translation_vector = cv2.solvePnP(
            model_points,
            image_points,
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )
        
        if not success:
            return 0.0
            
        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
        # Decompose the rotation matrix to extract angles
        projection_matrix = np.hstack((rotation_matrix, translation_vector))
        _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(projection_matrix)
        
        # euler_angles has pitch, yaw, roll in degrees
        yaw = float(euler_angles[1, 0])
        return yaw
    except Exception:
        return 0.0

def verify_liveness(frames_bytes_list: List[bytes], challenge: str) -> bool:
    """
    Verifies if a list of captured frames satisfies the anti-spoofing liveness challenge.
    challenge in ['blink', 'smile', 'turn_left', 'turn_right']
    """
    if not frames_bytes_list:
        return False
        
    app = get_face_analysis_app()
    
    if challenge == 'blink':
        consecutive_blinks = 0
        for frame_bytes in frames_bytes_list:
            try:
                nparr = np.frombuffer(frame_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    continue
                faces = app.get(img)
                if not faces:
                    continue
                
                landmarks = faces[0].landmark
                ear = calculate_ear(landmarks)
                
                # EAR < 0.2 indicates blink
                if ear < 0.2:
                    consecutive_blinks += 1
                else:
                    if consecutive_blinks >= 2:
                        return True
                    consecutive_blinks = 0
            except Exception:
                continue
        # Fallback check if the blink happened at the end of the sequence
        return consecutive_blinks >= 2
        
    elif challenge == 'smile':
        for frame_bytes in frames_bytes_list:
            try:
                nparr = np.frombuffer(frame_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    continue
                
                # Analyze using DeepFace
                result = DeepFace.analyze(img, actions=['emotion'], enforce_detection=False)
                if not result:
                    continue
                    
                # DeepFace analyze output is a list if multiple faces, or single dict
                data = result[0] if isinstance(result, list) else result
                happy_score = data.get('emotion', {}).get('happy', 0.0)
                
                # Smile is verified if happy confidence is > 60%
                if happy_score > 60.0:
                    return True
            except Exception:
                continue
        return False
        
    elif challenge == 'turn_left':
        for frame_bytes in frames_bytes_list:
            try:
                nparr = np.frombuffer(frame_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    continue
                faces = app.get(img)
                if not faces:
                    continue
                
                landmarks = faces[0].landmark
                yaw = estimate_head_pose(landmarks, img.shape)
                
                # Turning left results in negative yaw angle (yaw < -15 degrees)
                if yaw < -15.0:
                    return True
            except Exception:
                continue
        return False
        
    elif challenge == 'turn_right':
        for frame_bytes in frames_bytes_list:
            try:
                nparr = np.frombuffer(frame_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    continue
                faces = app.get(img)
                if not faces:
                    continue
                
                landmarks = faces[0].landmark
                yaw = estimate_head_pose(landmarks, img.shape)
                
                # Turning right results in positive yaw angle (yaw > 15 degrees)
                if yaw > 15.0:
                    return True
            except Exception:
                continue
        return False
        
    return False
