from __future__ import annotations

"""
Eightfold AI - Application Configuration

Centralizes all application settings using Pydantic BaseSettings
for type-safe, environment-variable-driven configuration.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    # Server
    app_name: str = "Eightfold AI - Candidate Data Transformer"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Pipeline defaults
    default_phone_region: str = "IN"
    max_file_size_mb: int = 50
    max_files_per_upload: int = 20

    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "text"

    model_config = {"env_prefix": "EIGHTFOLD_", "env_file": ".env"}


settings = Settings()
