"""Application settings, read from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # No defaults: a missing variable must stop the app at startup, not fail later.
    database_url: str


settings = Settings()
