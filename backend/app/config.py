import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # GitHub OAuth
    github_client_id: str | None = None
    github_client_secret: str | None = None
    github_oauth_callback_url: str = "http://localhost:8001/api/auth/github/callback"

    # Legacy token for public API access (fallback)
    github_token: str | None = None

    # Encryption key for token storage (Fernet key)
    encryption_key: str | None = None

    # Database
    database_url: str = "postgresql+psycopg2://postgres:asep_password@localhost:5432/asep"

    # Frontend URL (for CORS and redirects)
    frontend_url: str = "chrome-extension://*"

    # Repository Ingestion Limits (Phase 6)
    max_file_count: int = 50000
    max_file_size_mb: int = 10
    max_total_size_mb: int = 500
    max_execution_time_seconds: int = 300
    max_disk_usage_mb: int = 1000
    shallow_clone_depth: int = 1  # 1 for shallow, 0 for full history
    excluded_patterns: List[str] = [
        "node_modules/", ".git/", "dist/", "build/", "__pycache__/",
        ".venv/", "venv/", "env/", ".next/", ".nuxt/", "target/",
        "bin/", "obj/", ".idea/", ".vscode/", "*.min.js", "*.min.css",
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "*.log",
        "*.tsbuildinfo", "coverage/", ".coverage", "htmlcov/",
        ".pytest_cache/", ".mypy_cache/", ".tox/", "*.egg-info/",
        "vendor/", "bower_components/", "jspm_packages/",
    ]


settings = Settings()
