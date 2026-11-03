"""
Application Configuration Module.
Loads environment variables and system settings.
"""

from pathlib import Path
import os
from typing import List, Union
from dotenv import load_dotenv

# Locate base directories
backend_dir = Path(__file__).resolve().parent
root_dir = backend_dir.parent

# Load .env file from root or backend directory if present
if (root_dir / ".env").exists():
    load_dotenv(root_dir / ".env")
if (backend_dir / ".env").exists():
    load_dotenv(backend_dir / ".env")
load_dotenv()

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import field_validator

    class Settings(BaseSettings):
        PROJECT_NAME: str = "Industrial Predictive Maintenance System"
        API_V1_PREFIX: str = "/api/v1"
        DEBUG: bool = True

        # PostgreSQL Connection Components
        POSTGRES_USER: str = "postgres"
        POSTGRES_PASSWORD: str = ""
        POSTGRES_SERVER: str = "localhost"
        POSTGRES_PORT: int = 5432
        POSTGRES_DB: str = "industrial_maintenance"

        # Full Database URL (assembled or overridden via .env)
        DATABASE_URL: str = ""

        # CORS
        CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

        @field_validator("DATABASE_URL", mode="before")
        def assemble_db_connection(cls, v: str, info) -> str:
            if isinstance(v, str) and v.strip() and "${" not in v and v.count("@") <= 1:
                return v

            import urllib.parse
            user = info.data.get("POSTGRES_USER", "postgres")
            password = info.data.get("POSTGRES_PASSWORD", "")
            server = info.data.get("POSTGRES_SERVER", "localhost")
            port = info.data.get("POSTGRES_PORT", 5432)
            db = info.data.get("POSTGRES_DB", "industrial_maintenance")

            pwd_part = f":{urllib.parse.quote_plus(password)}" if password else ""
            return f"postgresql://{user}{pwd_part}@{server}:{port}/{db}"

        @field_validator("CORS_ORIGINS", mode="before")
        def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
            if isinstance(v, str):
                import json
                if v.startswith("["):
                    try:
                        return json.loads(v)
                    except Exception:
                        pass
                return [i.strip() for i in v.split(",") if i.strip()]
            elif isinstance(v, list):
                return v
            return []

        model_config = SettingsConfigDict(
            env_file=[str(root_dir / ".env"), str(backend_dir / ".env"), ".env"],
            env_file_encoding="utf-8",
            case_sensitive=True,
            extra="ignore",
        )

except ImportError:
    from pydantic import BaseModel, Field

    class Settings(BaseModel):
        PROJECT_NAME: str = Field(default_factory=lambda: os.getenv("PROJECT_NAME", "Industrial Predictive Maintenance System"))
        API_V1_PREFIX: str = Field(default_factory=lambda: os.getenv("API_V1_PREFIX", "/api/v1"))
        DEBUG: bool = Field(default_factory=lambda: os.getenv("DEBUG", "True").lower() in ("true", "1", "yes"))

        POSTGRES_USER: str = Field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
        POSTGRES_PASSWORD: str = Field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", ""))
        POSTGRES_SERVER: str = Field(default_factory=lambda: os.getenv("POSTGRES_SERVER", "localhost"))
        POSTGRES_PORT: int = Field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
        POSTGRES_DB: str = Field(default_factory=lambda: os.getenv("POSTGRES_DB", "industrial_maintenance"))

        DATABASE_URL: str = Field(default_factory=lambda: (
            os.getenv("DATABASE_URL") if (os.getenv("DATABASE_URL") and "${" not in os.getenv("DATABASE_URL") and os.getenv("DATABASE_URL").count("@") <= 1) else
            f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}"
            f"{':' + __import__('urllib.parse').parse.quote_plus(os.getenv('POSTGRES_PASSWORD', '')) if os.getenv('POSTGRES_PASSWORD') else ''}"
            f"@{os.getenv('POSTGRES_SERVER', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}"
            f"/{os.getenv('POSTGRES_DB', 'industrial_maintenance')}"
        ))

        CORS_ORIGINS: List[str] = Field(default_factory=lambda: [
            origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if origin.strip()
        ])


settings = Settings()
