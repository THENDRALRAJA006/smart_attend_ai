"""
SmartAttend AI — Master Embedding Generation Service

Enterprise-grade biometric registration pipeline:
  1. Quality filtering (blur, brightness, face size, angle, confidence)
  2. ArcFace embedding extraction (one-by-one for memory efficiency)
  3. Outlier removal (embeddings too dissimilar from the cohort)
  4. Deduplication (remove near-identical embeddings)
  5. Master embedding generation (L2-normalised mean)

No images are ever written to disk.
All image buffers are freed immediately after embedding extraction.
"""
import gc
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np

from app.config.config import settings
from app.utils.face_utils import get_face_analysis_app
from app.utils.embedding_utils import cosine_similarity

logger = logging.getLogger("smartattend.embedding_service")


@dataclass
class EmbeddingResult:
    """Result of the master embedding pipeline."""
    master_embedding: np.ndarray
    quality_score: float
    valid_count: int
    total_processed: int
    rejected_count: int


@dataclass
class _FrameCandidate:
    """Internal: a single frame that passed quality checks."""
    embedding: np.ndarray
    det_score: float
    sharpness: float


class EmbeddingService:
    """
    Stateless service for generating master embeddings from raw image frames.

    Designed for Google Cloud Run:
      - Processes frames one-by-one to minimise peak RAM usage.
      - Frees image buffers immediately after embedding extraction.
      - Never holds all 150 images in memory simultaneously.
    """

    def __init__(self):
        self._app = None

    @property
    def face_app(self):
        """Lazy-load the InsightFace model."""
        if self._app is None:
            self._app = get_face_analysis_app()
        return self._app

    # ── Public API ────────────────────────────────────────────────────────────

    def generate_master_embedding(
        self,
        frames: List[bytes],
        sharpness_threshold: float = settings.SHARPNESS_THRESHOLD,
        det_confidence_threshold: float = settings.DETECTION_CONFIDENCE_THRESHOLD,
        dedup_threshold: float = settings.DEDUP_SIMILARITY_THRESHOLD,
        min_valid: int = settings.MIN_VALID_EMBEDDINGS,
    ) -> EmbeddingResult:
        """
        Generate a single master embedding from a list of raw image frames.

        Args:
            frames: Raw JPEG/PNG bytes for each captured frame.
            sharpness_threshold: Minimum Laplacian variance for sharpness.
            det_confidence_threshold: Minimum ArcFace detection confidence.
            dedup_threshold: Max cosine similarity before treating as duplicate.
            min_valid: Minimum number of valid embeddings required.

        Returns:
            EmbeddingResult with the L2-normalised master embedding.

        Raises:
            ValueError: If too few valid embeddings could be extracted.
        """
        logger.info(
            "Starting master embedding pipeline for %d frames", len(frames)
        )

        # Step 1 & 2: Quality filter + extract embeddings (one-by-one)
        candidates = self._extract_candidates(
            frames,
            sharpness_threshold=sharpness_threshold,
            det_confidence_threshold=det_confidence_threshold,
        )
        logger.info(
            "Quality filtering: %d/%d frames passed", len(candidates), len(frames)
        )

        if len(candidates) < min_valid:
            raise ValueError(
                f"Only {len(candidates)} high-quality embeddings extracted "
                f"(minimum {min_valid} required). Please retry in better "
                f"lighting with all guided poses completed."
            )

        # Step 3: Outlier removal
        candidates = self._remove_outliers(candidates)
        logger.info("After outlier removal: %d embeddings remain", len(candidates))

        if len(candidates) < min_valid:
            raise ValueError(
                f"Only {len(candidates)} embeddings after outlier removal "
                f"(minimum {min_valid} required). Registration images may be "
                f"inconsistent. Please retry."
            )

        # Step 4: Deduplication
        candidates = self._deduplicate(candidates, threshold=dedup_threshold)
        logger.info("After deduplication: %d embeddings remain", len(candidates))

        # Step 5: Generate master embedding
        master_emb = self._compute_master_embedding(
            [c.embedding for c in candidates]
        )
        quality_score = float(np.mean([c.det_score for c in candidates]))

        logger.info(
            "Master embedding generated: quality=%.4f, from %d embeddings",
            quality_score,
            len(candidates),
        )

        return EmbeddingResult(
            master_embedding=master_emb,
            quality_score=quality_score,
            valid_count=len(candidates),
            total_processed=len(frames),
            rejected_count=len(frames) - len(candidates),
        )

    # ── Step 1 & 2: Quality Filtering + Embedding Extraction ─────────────────

    def _extract_candidates(
        self,
        frames: List[bytes],
        sharpness_threshold: float,
        det_confidence_threshold: float,
    ) -> List[_FrameCandidate]:
        """
        Process frames ONE-BY-ONE for memory efficiency.
        Each frame is decoded, quality-checked, embedding-extracted, then freed.
        """
        candidates: List[_FrameCandidate] = []

        for i, frame_bytes in enumerate(frames):
            try:
                candidate = self._process_single_frame(
                    frame_bytes,
                    sharpness_threshold=sharpness_threshold,
                    det_confidence_threshold=det_confidence_threshold,
                )
                if candidate is not None:
                    candidates.append(candidate)
            except Exception as e:
                logger.debug("Frame %d skipped: %s", i, str(e))
            finally:
                # Explicitly free the frame bytes reference
                frames[i] = None  # type: ignore[call-overload]

            # Periodic garbage collection (every 25 frames)
            if (i + 1) % 25 == 0:
                gc.collect()

        # Final cleanup
        gc.collect()
        return candidates

    def _process_single_frame(
        self,
        frame_bytes: bytes,
        sharpness_threshold: float,
        det_confidence_threshold: float,
    ) -> Optional[_FrameCandidate]:
        """
        Process a single frame: decode → quality checks → embedding extraction.
        Returns None if the frame fails any quality gate.
        """
        # Decode image
        nparr = np.frombuffer(frame_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return None

        # Quality Check 1: Sharpness (Laplacian variance)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if sharpness < sharpness_threshold:
            del img, gray
            return None

        # Quality Check 2: Brightness
        mean_brightness = float(gray.mean())
        del gray  # Free grayscale buffer immediately
        if mean_brightness < settings.BRIGHTNESS_MIN or mean_brightness > settings.BRIGHTNESS_MAX:
            del img
            return None

        # Face detection
        faces = self.face_app.get(img)
        if not faces:
            del img
            return None

        face = max(faces, key=lambda f: f.det_score)

        # Quality Check 3: Detection confidence
        if face.det_score < det_confidence_threshold:
            del img
            return None

        # Quality Check 4: Face bounding box size
        bbox = face.bbox  # [x1, y1, x2, y2]
        face_width = bbox[2] - bbox[0]
        face_height = bbox[3] - bbox[1]
        if face_width < settings.MIN_FACE_SIZE or face_height < settings.MIN_FACE_SIZE:
            del img
            return None

        # Quality Check 5: Head pose angle (yaw)
        if hasattr(face, "pose") and face.pose is not None:
            yaw = abs(face.pose[1]) if len(face.pose) > 1 else 0.0
            pitch = abs(face.pose[0]) if len(face.pose) > 0 else 0.0
            if yaw > settings.MAX_FACE_YAW or pitch > settings.MAX_FACE_PITCH:
                del img
                return None

        embedding = face.normed_embedding  # 512-dim float32

        # Free image buffer immediately after extraction
        del img, faces

        return _FrameCandidate(
            embedding=embedding,
            det_score=float(face.det_score),
            sharpness=sharpness,
        )

    # ── Step 3: Outlier Removal ──────────────────────────────────────────────

    def _remove_outliers(
        self,
        candidates: List[_FrameCandidate],
        threshold: float = settings.OUTLIER_SIMILARITY_THRESHOLD,
    ) -> List[_FrameCandidate]:
        """
        Remove embeddings whose mean cosine similarity to all other
        embeddings is below the threshold (likely wrong face or noise).
        """
        if len(candidates) <= 2:
            return candidates

        embeddings = np.array([c.embedding for c in candidates], dtype=np.float32)
        # Compute pairwise similarities via matrix multiplication
        # (embeddings are already L2-normalised by InsightFace)
        sim_matrix = embeddings @ embeddings.T  # (N, N)

        # Mean similarity per embedding (excluding self-similarity)
        n = len(candidates)
        np.fill_diagonal(sim_matrix, 0.0)
        mean_sims = sim_matrix.sum(axis=1) / (n - 1)

        filtered = [
            c for c, mean_sim in zip(candidates, mean_sims)
            if mean_sim >= threshold
        ]

        removed_count = len(candidates) - len(filtered)
        if removed_count > 0:
            logger.info("Removed %d outlier embeddings", removed_count)

        return filtered

    # ── Step 4: Deduplication ────────────────────────────────────────────────

    def _deduplicate(
        self,
        candidates: List[_FrameCandidate],
        threshold: float,
    ) -> List[_FrameCandidate]:
        """
        Greedily remove near-duplicate embeddings (cosine > threshold).
        Keeps embeddings with highest detection confidence first.
        """
        # Sort by detection confidence descending
        sorted_candidates = sorted(
            candidates, key=lambda c: c.det_score, reverse=True
        )

        kept: List[_FrameCandidate] = []
        for candidate in sorted_candidates:
            if all(
                cosine_similarity(candidate.embedding, k.embedding) < threshold
                for k in kept
            ):
                kept.append(candidate)

        return kept

    # ── Step 5: Master Embedding Computation ─────────────────────────────────

    @staticmethod
    def _compute_master_embedding(
        embeddings: List[np.ndarray],
    ) -> np.ndarray:
        """
        Compute the master embedding as the L2-normalised mean of all
        input embeddings.

        This is the standard approach used in production biometric systems
        (FaceNet, ArcFace papers). The mean of normalised embeddings
        represents the centroid of the face's identity cluster in the
        512-dimensional embedding space.
        """
        stacked = np.array(embeddings, dtype=np.float32)  # (N, 512)
        mean_emb = stacked.mean(axis=0)  # (512,)

        # L2-normalise the result
        norm = np.linalg.norm(mean_emb)
        if norm > 0:
            mean_emb = mean_emb / norm

        return mean_emb


# ── Module-level singleton ───────────────────────────────────────────────────
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the singleton EmbeddingService instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
