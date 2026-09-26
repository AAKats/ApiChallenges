from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    api_base_url: str = 'https://apichallenges.com'
    api_timeout_seconds: float = 15.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
