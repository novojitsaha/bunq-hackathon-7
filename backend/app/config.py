from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    database_url: str = Field(default="sqlite:///./app.db", alias="DATABASE_URL")
    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model_receipt: str | None = Field(default=None, alias="OPENAI_MODEL_RECEIPT")
    openai_request_timeout_seconds: int = Field(default=45, alias="OPENAI_REQUEST_TIMEOUT_SECONDS")

    open_food_facts_live: bool = Field(default=False, alias="OPEN_FOOD_FACTS_LIVE")
    open_food_facts_user_agent: str = Field(
        default="BunqBiteBalance/0.1 hackathon-demo contact:local@example.invalid",
        alias="OPEN_FOOD_FACTS_USER_AGENT",
    )

    bunq_api_key: str | None = Field(default=None, alias="BUNQ_API_KEY")
    bunq_callback_url: str | None = Field(default=None, alias="BUNQ_CALLBACK_URL")


@lru_cache
def get_settings() -> Settings:
    return Settings()

