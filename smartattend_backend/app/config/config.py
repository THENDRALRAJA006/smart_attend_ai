from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional


class Settings(BaseSettings):
    # ── AWS RDS MySQL Connection ───────────────────────────────────────────────
    DATABASE_URL: Optional[str] = None

    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "smartattend"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""

    # ── JWT ──────────────────────────────────────────────────────────────────────
    JWT_SECRET: str = "your-super-secret-key-min-32-chars-change-in-production"
    JWT_ALGORITHM: str = "HS256"

    # ── ArcFace / InsightFace ────────────────────────────────────────────────────
    ARCFACE_MODEL_NAME: str = "buffalo_l"

    # ── Environment ─────────────────────────────────────────────────────────────
    ENVIRONMENT: str = "production"

    # ── Face Registration Tuning ─────────────────────────────────────────────────
    MAX_FACE_EMBEDDINGS: int = 50
    MIN_FRAMES_FOR_REGISTRATION: int = 20
    SHARPNESS_THRESHOLD: float = 100.0
    DETECTION_CONFIDENCE_THRESHOLD: float = 0.95
    DEDUP_SIMILARITY_THRESHOLD: float = 0.98

    # ── Liveness ─────────────────────────────────────────────────────────────────
    LIVENESS_TOKEN_EXPIRY_MINUTES: int = 3

    # ── Attendance Similarity Thresholds ────────────────────────────────────────
    SIMILARITY_THRESHOLD_PRESENT: float = 0.75
    SIMILARITY_THRESHOLD_REVIEW: float = 0.65

    # ── Rate Limiting ────────────────────────────────────────────────────────────
    MAX_VERIFICATION_ATTEMPTS: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_mysql_url(cls, v: Optional[str]) -> Optional[str]:
        """Normalise DATABASE_URL to pymysql driver string."""
        if v:
            # Replace postgres-style prefixes that sometimes leak from env
            for prefix in ("postgresql+psycopg2://", "postgresql://", "postgres://"):
                if v.startswith(prefix):
                    v = "mysql+pymysql://" + v[len(prefix):]
            # Ensure correct MySQL driver prefix
            if not v.startswith("mysql+pymysql://"):
                v = v.replace("mysql://", "mysql+pymysql://")
            return v
        return None

    def model_post_init(self, __context):
        """Build DATABASE_URL from components if not provided directly."""
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
                f"?charset=utf8mb4"
            )


settings = Settings()
