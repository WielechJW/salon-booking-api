from functools import lru_cache
from secrets import token_urlsafe
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(
        default="sqlite:///./salon.db",
        min_length=1,
    )
    salon_timezone: str = Field(default="Europe/Warsaw", min_length=1)
    jwt_secret_key: SecretStr = Field(
        default_factory=lambda: SecretStr(token_urlsafe(32)), min_length=32
    )
    access_token_expire_minutes: int = Field(default=30, gt=0, le=1440)

    @field_validator("salon_timezone")
    @classmethod
    def validate_salon_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("Unknown IANA timezone") from error

        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
