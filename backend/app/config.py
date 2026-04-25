"""
PD2MD Configuration Module.

Centralized settings for the entire application, loaded from environment
variables with sensible defaults for local development.
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application-wide configuration."""

    # Server
    app_name: str = "PD2MD"
    app_version: str = "0.1.0"
    debug: bool = True
    host: str = "127.0.0.1"
    port: int = 8000

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    output_dir: Path = base_dir / "output"
    upload_dir: Path = base_dir / "output" / "uploads"

    # Processing
    max_file_size_mb: int = 100
    max_pages: int = 2000
    default_image_format: str = "png"  # "png" or "jpeg"
    image_dpi: int = 150
    jpeg_quality: int = 85

    # Timeouts
    page_timeout_seconds: int = 300

    model_config = {"env_prefix": "PD2MD_"}


settings = Settings()
