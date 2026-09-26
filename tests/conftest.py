import os
from collections.abc import Callable, Iterator

import httpx
import pytest

from api_challenges.assertions import (
    assert_content_type,
    assert_status_code,
    assert_valid_guid,
)
from api_challenges.clients import (
    BASIC_AUTHORIZATION,
    CHALLENGER_HEADER,
    SECRET_PATH,
    TODOS_PATH,
    BaseClient,
)
from api_challenges.config import Settings, get_settings
from api_challenges.utils import todo_from_xml


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


@pytest.fixture
def todo_factory(api_client) -> Iterator[Callable[..., tuple[httpx.Response, dict]]]:
    created_ids: list[int] = []

    def _create(**kwargs: object) -> tuple[httpx.Response, dict]:
        response = api_client.post(TODOS_PATH, **kwargs)
        assert_status_code(response=response, expected_status_code=201)
        content_type = response.headers.get('content-type', '')
        payload = response.json() if 'json' in content_type else todo_from_xml(response.text)
        created_ids.append(payload['id'])
        return response, payload

    yield _create

    for todo_id in created_ids:
        api_client.delete(f'{TODOS_PATH}/{todo_id}')


@pytest.fixture
def auth_token(api_client) -> tuple[httpx.Response, str]:
    response = api_client.get(
        f'{SECRET_PATH}/token',
        headers={'Authorization': BASIC_AUTHORIZATION, 'Accept': '*/*'},
    )
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    token = response.json()['token']
    assert_valid_guid(token)
    return response, token


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        '--challenge',
        type=int,
        metavar='N',
        help='run only tests for challenge number N (value of challenge(N) marker)',
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    challenge = config.getoption('--challenge')
    if challenge is not None:
        items[:] = [
            item
            for item in items
            if (marker := item.get_closest_marker('challenge')) is not None
            and marker.args
            and int(marker.args[0]) == challenge
        ]
        if not items:
            pytest.fail(f'No tests found for --challenge {challenge}', pytrace=False)

    def _challenge_number(item: pytest.Item) -> float:
        marker = item.get_closest_marker('challenge')
        if marker is None or not marker.args:
            return float('inf')
        return float(marker.args[0])

    items.sort(key=_challenge_number)
