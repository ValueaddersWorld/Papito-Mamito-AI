"""Environment-backed settings for Papito Mamito."""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PapitoSettings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    suno_api_key: str | None = Field(default=None, alias="SUNO_API_KEY")
    suno_base_url: str = Field(default="https://api.suno.ai", alias="SUNO_BASE_URL")
    suno_model: str = Field(default="chirp-v3.5", alias="SUNO_MODEL")
    suno_timeout: float = Field(default=30.0, alias="SUNO_TIMEOUT")

    api_keys_raw: str | None = Field(default=None, alias="PAPITO_API_KEYS")
    api_rate_limit_per_min: int = Field(default=60, alias="PAPITO_API_RATE_LIMIT_PER_MIN")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def api_keys(self) -> List[str]:
        if not self.api_keys_raw:
            return []
        return [key.strip() for key in self.api_keys_raw.split(",") if key.strip()]

    @property
    def api_keys_set(self) -> set[str]:
        return set(self.api_keys)


@lru_cache(maxsize=1)
def get_settings() -> PapitoSettings:
    """Return cached settings instance."""

    return PapitoSettings()
