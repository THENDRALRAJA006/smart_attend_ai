from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional

class Settings(BaseSettings):
    DB_HOST: str = "db.supabase.co"
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_SSLMODE: str = "require"
    
    DATABASE_URL: Optional[str] = None
    
    # Supabase specific environment variables
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SECRET_KEY: Optional[str] = None
    
    JWT_SECRET: str = "your-super-secret-key-min-32-chars-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ENVIRONMENT: str = "production"
    
    LIVENESS_TOKEN_EXPIRY_MINUTES: int = 3
    SIMILARITY_THRESHOLD_PRESENT: float = 0.80
    SIMILARITY_THRESHOLD_REVIEW: float = 0.65

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: Optional[str]) -> Optional[str]:
        if v:
            # Ensure correct PostgreSQL driver prefix for psycopg2
            if v.startswith("postgresql://"):
                v = v.replace("postgresql://", "postgresql+psycopg2://")
            # Enforce sslmode if not specified in url
            if "sslmode=" not in v:
                separator = "&" if "?" in v else "?"
                v = f"{v}{separator}sslmode=require"
            return v
        return None

    def model_post_init(self, __context):
        if not self.DATABASE_URL:
            ssl_suffix = f"?sslmode={self.DB_SSLMODE}" if self.DB_SSLMODE else ""
            self.DATABASE_URL = f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}{ssl_suffix}"

settings = Settings()
