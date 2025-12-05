"""Environment-backed settings for Papito Mamito."""

from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PapitoSettings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    # ============== Suno AI (Music Generation) ==============
    suno_api_key: str | None = Field(default=None, alias="SUNO_API_KEY")
    suno_base_url: str = Field(default="https://api.suno.ai", alias="SUNO_BASE_URL")
    suno_model: str = Field(default="chirp-v3.5", alias="SUNO_MODEL")
    suno_timeout: float = Field(default=30.0, alias="SUNO_TIMEOUT")

    # ============== API Security ==============
    api_keys_raw: str | None = Field(default=None, alias="PAPITO_API_KEYS")
    api_rate_limit_per_min: int = Field(default=60, alias="PAPITO_API_RATE_LIMIT_PER_MIN")

    # ============== Firebase ==============
    firebase_project_id: str | None = Field(default=None, alias="FIREBASE_PROJECT_ID")
    firebase_service_account_path: str | None = Field(
        default=None, 
        alias="FIREBASE_SERVICE_ACCOUNT_PATH",
        description="Path to Firebase service account JSON file"
    )
    # Alternative: inline credentials (base64 encoded JSON)
    firebase_credentials_json: str | None = Field(
        default=None, 
        alias="FIREBASE_CREDENTIALS_JSON",
        description="Base64 encoded Firebase service account JSON"
    )

    # ============== Instagram / Meta Graph API ==============
    instagram_access_token: str | None = Field(default=None, alias="INSTAGRAM_ACCESS_TOKEN")
    instagram_business_id: str | None = Field(default=None, alias="INSTAGRAM_BUSINESS_ID")
    instagram_app_id: str | None = Field(default=None, alias="INSTAGRAM_APP_ID")
    instagram_app_secret: str | None = Field(default=None, alias="INSTAGRAM_APP_SECRET")

    # ============== X / Twitter API ==============
    x_api_key: str | None = Field(default=None, alias="X_API_KEY")
    x_api_secret: str | None = Field(default=None, alias="X_API_SECRET")
    x_access_token: str | None = Field(default=None, alias="X_ACCESS_TOKEN")
    x_access_token_secret: str | None = Field(default=None, alias="X_ACCESS_TOKEN_SECRET")
    x_bearer_token: str | None = Field(default=None, alias="X_BEARER_TOKEN")

    # ============== Buffer (Fallback Scheduler) ==============
    buffer_access_token: str | None = Field(default=None, alias="BUFFER_ACCESS_TOKEN")
    buffer_profile_ids: str | None = Field(
        default=None, 
        alias="BUFFER_PROFILE_IDS",
        description="Comma-separated Buffer profile IDs"
    )

    # ============== OpenAI (AI Responses) ==============
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    # ============== Anthropic Claude (Alternative AI) ==============
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-haiku-20240307", alias="ANTHROPIC_MODEL")

    # ============== Telegram Notifications ==============
    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = Field(default=None, alias="TELEGRAM_CHAT_ID")

    # ============== Discord Notifications ==============
    discord_webhook_url: str | None = Field(default=None, alias="DISCORD_WEBHOOK_URL")

    # ============== Agent Configuration ==============
    agent_timezone: str = Field(default="Africa/Lagos", alias="AGENT_TIMEZONE")
    agent_morning_hour: int = Field(default=8, alias="AGENT_MORNING_HOUR")
    agent_afternoon_hour: int = Field(default=14, alias="AGENT_AFTERNOON_HOUR")
    agent_evening_hour: int = Field(default=20, alias="AGENT_EVENING_HOUR")
    agent_auto_approve_ratio: float = Field(
        default=0.8, 
        alias="AGENT_AUTO_APPROVE_RATIO",
        description="Ratio of content to auto-approve (0.0 to 1.0)"
    )

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

    @property
    def buffer_profile_id_list(self) -> List[str]:
        """Parse comma-separated Buffer profile IDs."""
        if not self.buffer_profile_ids:
            return []
        return [pid.strip() for pid in self.buffer_profile_ids.split(",") if pid.strip()]

    def has_instagram_credentials(self) -> bool:
        """Check if Instagram API credentials are configured."""
        return bool(self.instagram_access_token and self.instagram_business_id)

    def has_x_credentials(self) -> bool:
        """Check if X/Twitter API credentials are configured."""
        return bool(
            self.x_api_key and 
            self.x_api_secret and 
            self.x_access_token and 
            self.x_access_token_secret
        )

    def has_firebase_credentials(self) -> bool:
        """Check if Firebase credentials are configured."""
        return bool(self.firebase_service_account_path or self.firebase_credentials_json)

    def has_ai_credentials(self) -> bool:
        """Check if any AI API credentials are configured."""
        return bool(self.openai_api_key or self.anthropic_api_key)


@lru_cache(maxsize=1)
def get_settings() -> PapitoSettings:
    """Return cached settings instance."""

    return PapitoSettings()

