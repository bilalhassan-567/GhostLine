"""Runtime configuration, loaded from environment / .env.

Nothing secret is ever logged or echoed. `CALLE_API_KEY` and `LLM_API_KEY` stay in memory.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # A blank env var (e.g. one Vercel auto-creates from .env.example) falls back to the
        # field default instead of failing to parse.
        env_ignore_empty=True,
    )

    # --- CALL-E ---
    calle_api_key: str = Field(default="", alias="CALLE_API_KEY")
    calle_base_url: str = Field(default="https://api.heycall-e.com", alias="CALLE_BASE_URL")

    # --- LLM extractor ---
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(default="claude-sonnet-4-5", alias="LLM_MODEL")

    # --- safety / budget ---
    mode: str = Field(default="replay", alias="GHOSTLINE_MODE")  # "replay" | "live"
    webhook_base: str = Field(default="", alias="GHOSTLINE_WEBHOOK_BASE")  # public https base
    calle_webhook_secret: str = Field(default="", alias="CALLE_WEBHOOK_SECRET")
    credit_floor: int = Field(default=10, alias="GHOSTLINE_CREDIT_FLOOR")
    test_numbers_raw: str = Field(default="", alias="GHOSTLINE_TEST_NUMBERS")
    session_live_call_cap: int = Field(default=3, alias="GHOSTLINE_SESSION_LIVE_CALL_CAP")

    # --- call behaviour ---
    call_poll_interval_s: float = Field(default=4.0, alias="GHOSTLINE_POLL_INTERVAL_S")
    call_timeout_s: float = Field(default=600.0, alias="GHOSTLINE_CALL_TIMEOUT_S")
    business_hours_start: int = Field(default=9, alias="GHOSTLINE_BH_START")
    business_hours_end: int = Field(default=18, alias="GHOSTLINE_BH_END")

    @property
    def test_numbers(self) -> list[str]:
        return [n.strip() for n in self.test_numbers_raw.split(",") if n.strip()]

    @property
    def is_live(self) -> bool:
        return self.mode.lower() == "live"

    @property
    def has_calle(self) -> bool:
        return bool(self.calle_api_key)

    @property
    def has_llm(self) -> bool:
        return bool(self.llm_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
