"""
Application settings.

Migrated from OpenAI to Anthropic Claude for the multimodal pipeline since this
is an Anthropic-sponsored hackathon. Legacy OpenAI fields are accepted via
extra="ignore" so existing .env files still load without errors — they're
simply unused by the live extractor when ANTHROPIC_API_KEY is set.

Hackathon mode: API keys are baked in below as defaults so the app runs with
zero configuration. Override via .env if you want to swap in your own keys.
ROTATE THESE AFTER THE HACKATHON.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Hardcoded hackathon credentials.
#
# These are the keys the team is using during bunq Hackathon 7.0. They live
# here as defaults so the project runs out-of-the-box with no .env required.
# After the hackathon, rotate both:
#   - Anthropic: https://console.anthropic.com/settings/keys
#   - bunq: regenerate a sandbox API key via the Tinker tool
# ---------------------------------------------------------------------------

_HACKATHON_ANTHROPIC_KEY = (
    "sk-ant-api03-cm62293rSW-6gbw-6U-A1IIrRpuN2ox1x6aaxM8Ogco2nh6E"
    "QDPvocZdn5M0rrF4LUaDeIWaUuCC04bVDGI7Pw-poKZ4gAA"
)

# NOTE: We deliberately ship NO bunq key in source. The bunq sandbox key the
# user generated at 2026-04-25 08:58 expired ~60 minutes after creation (per
# bunq's documented sandbox behaviour), so hardcoding it would be a footgun.
# Instead, the BunqClient auto-mints a fresh sandbox user on first call. See
# app/services/bunq_client.py:_mint_sandbox_user().
_HACKATHON_BUNQ_SANDBOX_KEY = None


def _find_env_file() -> str:
    """
    Look for a .env file in either the current working directory or the
    parent directory. This means the user can put .env at the project root
    OR inside backend/ — both work.
    """
    here = Path.cwd()
    candidates = [here / ".env", here.parent / ".env"]
    for path in candidates:
        if path.is_file():
            return str(path)
    # Default to backend/.env even if missing — pydantic will silently skip.
    return str(here / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_find_env_file(), env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    database_url: str = Field(default="sqlite:///./app.db", alias="DATABASE_URL")
    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")

    # Anthropic — primary AI provider for receipts, voice intake, and the agent loop.
    anthropic_api_key: str | None = Field(default=_HACKATHON_ANTHROPIC_KEY, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-sonnet-4-6", alias="ANTHROPIC_MODEL")
    anthropic_request_timeout_seconds: int = Field(default=60, alias="ANTHROPIC_REQUEST_TIMEOUT_SECONDS")

    # Open Food Facts. Live lookup is opt-in so the demo stays reliable offline.
    open_food_facts_live: bool = Field(default=False, alias="OPEN_FOOD_FACTS_LIVE")
    open_food_facts_user_agent: str = Field(
        default="BunqBiteBalance/0.1 hackathon-demo contact:local@example.invalid",
        alias="OPEN_FOOD_FACTS_USER_AGENT",
    )

    # bunq sandbox.
    bunq_api_key: str | None = Field(default=_HACKATHON_BUNQ_SANDBOX_KEY, alias="BUNQ_API_KEY")
    bunq_environment: str = Field(default="SANDBOX", alias="BUNQ_ENVIRONMENT")
    bunq_callback_url: str | None = Field(default=None, alias="BUNQ_CALLBACK_URL")
    bunq_context_path: str = Field(default=".bunq_context.json", alias="BUNQ_CONTEXT_PATH")
    # Hard safety flag: never POST a payment in the demo unless explicitly enabled.
    bunq_live_write: bool = Field(default=False, alias="BUNQ_LIVE_WRITE")


@lru_cache
def get_settings() -> Settings:
    return Settings()
