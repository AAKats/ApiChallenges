"""Настройки подключения к стенду.

Значения читаются из переменных окружения, затем из .env, иначе берутся
дефолты из кода, поэтому прогон работает без .env.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Параметры обращения к API."""

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    api_base_url: str = 'https://apichallenges.com'
    api_timeout_seconds: float = 15.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Настройки подключения, создаваемые один раз на процесс.

    :return: закэшированный экземпляр Settings.
    """
    return Settings()
