from collections.abc import Iterator

import pytest

from api_challenges.clients import BaseClient
from api_challenges.config import Settings, get_settings


@pytest.fixture(scope='session')
def settings() -> Settings:
    return get_settings()

@pytest.fixture(scope='session')
def api_client(settings) -> Iterator[BaseClient]:
    client = BaseClient(
        base_url=settings.api_base_url,
        timeout=settings.api_timeout_seconds
    )
    client.create_challenger()
    print(f'X-CHALLENGER: {client.challenger}')
    yield client
    client.close()
