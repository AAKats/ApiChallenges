import os
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field

import allure
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
    CHALLENGES_PATH,
    SECRET_PATH,
    TODOS_PATH,
    BaseClient,
)
from api_challenges.config import Settings, get_settings
from api_challenges.utils import todo_from_xml

KNOWN_UNCREDITED = {
    'fresh': frozenset({70, 71, 75}),
    'restore': frozenset({75}),
}


@dataclass(frozen=True)
class Scoreboard:
    ran: frozenset[int]
    credited: int
    total: int
    unexpected: frozenset[int]
    uncredited_after_failure: frozenset[int]
    known: frozenset[int]
    stale: frozenset[int]


@dataclass
class _RunState:
    challenger: str | None = None
    challenge_by_nodeid: dict[str, int] = field(default_factory=dict)
    outcomes: dict[int, str] = field(default_factory=dict)
    skip_reason: str | None = None
    result: Scoreboard | None = None


_RUN = _RunState()


@pytest.fixture(scope='session')
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope='session')
def restore_guid() -> str | None:
    return os.environ.get('API_CHALLENGES_RESTORE_GUID') or None


@pytest.fixture(scope='session')
def api_client(settings, restore_guid) -> Iterator[BaseClient]:
    headers = {CHALLENGER_HEADER: restore_guid} if restore_guid else None
    client = BaseClient(
        base_url=settings.api_base_url, timeout=settings.api_timeout_seconds, headers=headers
    )
    with allure.step('Создание новой сессии challenger'):
        client.create_challenger()
    _RUN.challenger = client.challenger
    yield client
    client.close()


@pytest.fixture
def todo_factory(api_client) -> Iterator[Callable[..., tuple[httpx.Response, dict]]]:
    created_ids: list[int] = []

    def _create(**kwargs: object) -> tuple[httpx.Response, dict]:
        response, create_payload = _create_todo_with_retry(api_client, **kwargs)
        created_ids.append(create_payload['id'])
        return response, create_payload

    yield _create

    if created_ids:
        with allure.step('Очистка созданных todos'):
            for todo_id in created_ids:
                api_client.delete(f'{TODOS_PATH}/{todo_id}')


def _is_todo_visible(api_client: BaseClient, todo_id: int) -> bool:
    response = api_client.get(TODOS_PATH)
    assert_status_code(response=response, expected_status_code=200)
    return any(todo['id'] == todo_id for todo in response.json()['todos'])


def _create_todo_with_retry(
    api_client: BaseClient,
    *,
    attempts: int = 3,
    **kwargs: object,
) -> tuple[httpx.Response, dict]:
    for attempt in range(1, attempts + 1):
        with allure.step(f'Создание todo (попытка {attempt} из {attempts})'):
            response = api_client.post(TODOS_PATH, **kwargs)
        assert_status_code(response=response, expected_status_code=201)
        content_type = response.headers.get('content-type', '')
        payload = response.json() if 'json' in content_type else todo_from_xml(response.text)
        if _is_todo_visible(api_client, payload['id']):
            return response, payload
        with allure.step(f'Созданный todo {payload['id']} не виден в списке, удаляю и повторяю'):
            api_client.delete(f'{TODOS_PATH}/{payload['id']}')
    raise AssertionError(
        f'Failed to create a todo visible in GET {TODOS_PATH} after {attempts} attempts'
    )


@pytest.fixture
def auth_token(api_client) -> tuple[httpx.Response, str]:
    with allure.step('Получение auth token'):
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
    parser.addoption(
        '--scoreboard',
        action='store_true',
        help='verify after the run that no unexpected challenge stayed uncredited',
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
    _RUN.challenge_by_nodeid = {
        item.nodeid: int(marker.args[0])
        for item in items
        if (marker := item.get_closest_marker('challenge')) is not None and marker.args
    }


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    challenge = _RUN.challenge_by_nodeid.get(report.nodeid)
    if challenge is None:
        return
    if report.failed:
        _RUN.outcomes[challenge] = 'failed'
    elif report.passed:
        _RUN.outcomes.setdefault(challenge, 'passed')


def _xdist_workers(config: pytest.Config) -> int:
    if not config.pluginmanager.hasplugin('xdist'):
        return 0
    value = config.getoption('numprocesses', 0)
    if isinstance(value, int):
        return value
    return 1 if value else 0


def _fetch_challenges(settings: Settings, guid: str) -> list[dict]:
    with httpx.Client(
        base_url=settings.api_base_url,
        timeout=settings.api_timeout_seconds,
        headers={CHALLENGER_HEADER: guid},
    ) as client:
        response = client.get(CHALLENGES_PATH)
        response.raise_for_status()
        return response.json()['challenges']


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if not session.config.getoption('--scoreboard'):
        return
    if workers := _xdist_workers(session.config):
        _RUN.skip_reason = f'xdist splits the session across {workers} workers'
        return
    if _RUN.challenger is None:
        _RUN.skip_reason = 'no challenger session was created'
        return

    mode = 'restore' if os.environ.get('API_CHALLENGES_RESTORE_GUID') else 'fresh'
    known = KNOWN_UNCREDITED[mode]
    ran = frozenset(
        _RUN.challenge_by_nodeid[item.nodeid]
        for item in session.items
        if item.nodeid in _RUN.challenge_by_nodeid
    )
    try:
        challenges = _fetch_challenges(get_settings(), _RUN.challenger)
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        _RUN.skip_reason = f'GET {CHALLENGES_PATH} failed: {exc!r}'
        return

    uncredited = {item['id'] for item in challenges if not item['status']}
    scope = uncredited & ran
    unexpected = frozenset(i for i in scope - known if _RUN.outcomes.get(i) != 'failed')
    relevant_known = known & ran
    _RUN.result = Scoreboard(
        ran=ran,
        credited=len(challenges) - len(uncredited),
        total=len(challenges),
        unexpected=unexpected,
        uncredited_after_failure=frozenset(scope - known - unexpected),
        known=relevant_known,
        stale=frozenset(relevant_known - uncredited),
    )
    if unexpected:
        session.exitstatus = max(exitstatus, pytest.ExitCode.TESTS_FAILED)


def _format_ids(ids: frozenset[int]) -> str:
    return ', '.join(str(i) for i in sorted(ids)) or '—'


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter) -> None:
    if _RUN.skip_reason:
        terminalreporter.write_sep('-', f'scoreboard: disabled ({_RUN.skip_reason})')
        return
    if (result := _RUN.result) is None:
        return
    lines = [
        f'scoreboard: ran {len(result.ran)}, credited {result.credited} of {result.total}',
        f'  unexpected uncredited: {_format_ids(result.unexpected)}'
        + ('  <- FAIL' if result.unexpected else ''),
    ]
    if result.uncredited_after_failure:
        lines.append(
            f'  uncredited after test failure: {_format_ids(result.uncredited_after_failure)}'
        )
    lines.append(f'  known limitations:     {_format_ids(result.known)}')
    lines.append(f'  stale limitations:     {_format_ids(result.stale)}')
    terminalreporter.write_sep('-', 'scoreboard')
    for line in lines:
        terminalreporter.write_line(line)
