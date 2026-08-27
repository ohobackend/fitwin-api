from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    app_name: str = "FitTwin API"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://fitwin:fitwin@localhost:5432/fitwin"
    jwt_secret_key: str = Field(default="change-me-in-production", min_length=16)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    s3_endpoint_url: str | None = None
    s3_access_key_id: str = "minioadmin"
    s3_secret_access_key: str = "minioadmin"
    s3_bucket_name: str = "fitwin"
    s3_region: str = "us-east-1"
    s3_presigned_url_expire_seconds: int = 3600
    upload_max_bytes: int = 10 * 1024 * 1024
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_task_always_eager: bool = False
    celery_task_eager_propagates: bool = True
    ootdiffusion_path: str = "vendor/OOTDiffusion"
    ootdiffusion_gpu_id: int = 0
    ootdiffusion_steps: int = 20
    ootdiffusion_scale: float = 2.0
    ootdiffusion_seed: int = -1

@lru_cache
def get_settings() -> Settings:
    return Settings()
