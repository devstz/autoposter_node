from __future__ import annotations

import logging
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Config(BaseSettings):
    TOKEN: str = "TOKEN"
    DATABASE_URL: str = "DATABASE_URL"
    LOG_FILE: Path = Path("output.log")
    LOG_LEVEL: str = "INFO"
    GIT_REMOTE: str = "origin"
    GIT_BRANCH: str = "main"
    GIT_CHECK_INTERVAL_S: int = 300
    MAX_POSTS_PER_SECOND: int = 8  # Максимальное количество постов в секунду

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def base_dir(self) -> Path:
        return BASE_DIR

    @property
    def log_file_path(self) -> Path:
        return self._resolve_path(self.LOG_FILE)

    @property
    def log_level(self) -> int:
        level = getattr(logging, self.LOG_LEVEL.upper(), None)
        if isinstance(level, int):
            return level
        return logging.INFO

    @staticmethod
    def _resolve_path(value: Path) -> Path:
        if value.is_absolute():
            return value
        return BASE_DIR / value


settings = Config()


def get_settings() -> Config:
    return settings
