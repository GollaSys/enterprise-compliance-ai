from pydantic import BaseSettings, Field
from typing import Optional
import os

class Settings(BaseSettings):
    app_name: str = "Enterprise Compliance AI Platform"
    app_version: str = "1.0.0"
    app_env: str = Field(default="development", env="APP_ENV")

    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")

    chroma_host: str = Field(default="localhost", env="CHROMA_HOST")
    chroma_port: int = Field(default=8000, env="CHROMA_PORT")
    chroma_collection: str = Field(default="compliance_docs", env="CHROMA_COLLECTION")

    cors_origins: list = ["http://localhost:3000", "http://localhost:3001"]

    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_types: list = [".pdf", ".doc", ".docx", ".txt", ".csv", ".xlsx"]

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()