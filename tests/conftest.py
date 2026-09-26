import os
from collections.abc import Iterator

import pytest

from api_challenges.clients import CHALLENGER_HEADER, BaseClient
from api_challenges.config import Settings, get_settings


@pytest.fixture(scope='session')
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope='session')
def api_client(settings) -> Iterator[BaseClient]:
    restore_guid = os.environ.get('API_CHALLENGES_RESTORE_GUID')
    headers = {CHALLENGER_HEADER: restore_guid} if restore_guid else None
    client = BaseClient(
        base_url=settings.api_base_url, timeout=settings.api_timeout_seconds, headers=headers
    )
    client.create_challenger()
    yield client
    client.close()


def pytest_collection_modifyitems(
    items: list[pytest.Item],
) -> None:
    def _challenge_number(item: pytest.Item) -> float:
        marker = item.get_closest_marker('challenge')
        if marker is None or not marker.args:
            return float('inf')
        return float(marker.args[0])

    items.sort(key=_challenge_number)
