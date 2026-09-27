# API Challenges — REST API Test Automation

Автоматизация REST-тестирования веб-сервиса [API Challenges](https://apichallenges.com)
на `pytest` + `httpx`. Набор покрывает **все 99 челленджей** (id 1–99): каждый тест помечен
маркером `challenge(N)`, соответствующим номеру челленджа на сайте.

## Requirements

- [uv](https://docs.astral.sh/uv) — менеджер окружения и зависимостей
- Python >= 3.12
- Доступ к `https://apichallenges.com` (или локально поднятому серверу)

## Install

```bat
uv sync                 :: создать `.venv` и установить зависимости (вкл. dev-группу)
```

Активация `.venv` не обязательна — `uv run` сам находит окружение.

## Configuration

Настройки читаются через `pydantic-settings` из `.env` (файл в `.gitignore`):

| Переменная          | Значение по умолчанию     | Описание                        |
|---------------------|---------------------------|---------------------------------|
| `API_BASE_URL`      | `https://apichallenges.com` | Базовый URL тестируемого API  |
| `API_TIMEOUT_SECONDS` | `15`                      | Таймаут запроса, секунды       |

Необязательная переменная окружения `API_CHALLENGES_RESTORE_GUID` — переиспользование
существующей сессии challenger вместо создания новой (`tests/conftest.py:59-61`).
В штатных прогонах намеренно не используется — каждый прогон стартует со свежей сессии.

## Running tests

```bat
uv run pytest                     :: весь набор
uv run pytest -m smoke            :: быстрые проверки
uv run pytest -m regression       :: полный регресс
uv run pytest --challenge 36      :: конкретный челлендж
uv run pytest -k challenger       :: по имени теста
uv run pytest --scoreboard        :: полный набор + сверка кредитов
```

- Тесты сортируются по номеру челленджа автоматически (`tests/conftest.py`).
- `--challenge N` оставляет только тесты с маркером `challenge(N)` (реализовано в
  `tests/conftest.py:149-177`).
- Используется `--strict-markers`; маркеры `smoke`, `regression`, `positive`,
  `negative`, `challenge` объявлены в `pyproject.toml`.

## Project structure

```
src/api_challenges/
  clients.py      HTTP-клиент (httpx), обработка X-CHALLENGER, ApiError
  config.py       Настройки (pydantic-settings + .env)
  assertions.py   Проверки ответов и payload'ов
  utils.py        Парсинг XML/CSV/TSV/HTML
tests/
  conftest.py            Session-фикстуры api_client и settings, фикстуры
                         todo_factory и auth_token, фильтр --challenge
  test_start.py          1–2
  test_todos.py          3–6, 22–41, 45–69, 78–79, 98–103 и др.
  test_todo_filtration.py 7–21
  test_todo_query.py     42–44
  test_heartbeat.py      80–87
  test_secret.py         88–97
  test_challenger.py     70–77
pyproject.toml           Зависимости, конфиг pytest/ruff
```

## Fixtures

- `api_client` (session) — httpx-клиент с базовым URL, автоматическим
  переиспользованием `X-CHALLENGER` и генерацией `ApiError` на ошибки.
- `todo_factory` — создание todo с ретраем (до 3 попыток, каждая — отдельный шаг в
  Allure) и проверкой видимости в `GET /api/todos`; возвращает `(response, payload)`,
  при тесте автоматически удаляет созданные записи.
- `auth_token` — получение Bearer-токена secret-эндпоинта; возвращает `(response, token)`.

## Coverage & markers

Маппинг «тест → челлендж» задаётся декоратором:

```python
@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(36)
def test_100_put_no_id_body(todo_factory): ...
```

Все 99 челленджей (1–99) имеют соответствующий тест. Полный список и статусы можно
посмотреть через `GET /api/challenges` на сайте или в ответе теста `test_002`.

## Scoreboard

Опция `--scoreboard` после прогона читает `GET /api/challenges` и сверяет незасчитанные
челленджи с ожидаемыми, закрывая случай «тест зелёный, а кредита нет». Сверка живёт в
хуках `pytest_sessionfinish` / `pytest_terminal_summary` (`tests/conftest.py`), а не в
тесте, поэтому не зависит от порядка выполнения.

Учитываются только челленджи, тесты которых реально выполнялись в этом прогоне, — иначе
`-m smoke` и `--challenge 43` всегда давали бы ложные срабатывания:

```text
scoreboard: ran 99, credited 96 of 99
  unexpected uncredited: 43  <- FAIL
  uncredited after test failure: —
  known limitations:     70, 71, 75
  stale limitations:     —
```

- **unexpected uncredited** — незасчитан, тест при этом прошёл; прогон падает
  (ненулевой код возврата).
- **uncredited after test failure** — незасчитан, но тест и так упал; причина уже видна
  в падении, отдельного провала не добавляем.
- **known limitations** — ожидаемые незасчитанные для текущего режима.
- **stale limitations** — известное ограничение unexpectedly засчиталось (аналог XPASS);
  повод пересмотреть запись в Known limitations.

Сверка отключается с явным сообщением, если запущена под `pytest-xdist`: каждый воркер
создаёт свою сессию challenger, и кредиты распределяются между несколькими GUID, поэтому
сверка по одному из них дала бы ложные «незасчитанные». В CI опция включена только в
job'е `full-suite`.

## Known limitations

Три челленджа нельзя довести до pass на **свежей** throwaway-сессии одного прогона
(ограничения реализации сервера, а не тестов):

- **#70, #71** — `GET/POST /api/challenger`: сервер кредитует их только для сессий
  в состоянии `LOADED_FROM_PERSISTENCE` (session была выселена по простою >10 минут
  и пересоздана из хранилища). Свежая сессия этот кейс не порождает.
- **#75** — `PUT /api/challenger/{guid}` (create): кредит структурно привязан к
  **новому** challenger'у, созданному этим PUT (ответный `X-CHALLENGER`), а не к
  рабочей сессии, которая уже была создана через `POST /api/challenger`.

Поэтому максимальный трек на свежей сессии — **96/99** (False только #70, #71, #75).
Сами тесты для этих челленджей корректны и проходят; переиспользование сохранённой
сессии (env `API_CHALLENGES_RESTORE_GUID`) убирает ограничение для #70/#71,
для #75 — нет (кредит всегда уходит новому созданному guid).

Ожидаемые незасчитанные хранятся в `KNOWN_UNCREDITED` (`tests/conftest.py:25-28`) —
этот список использует и сверка scoreboard; при изменении ограничений стенда правится
он, а не этот раздел.

Дополнительно, live-стенд изредка «теряет» только что созданный todo: `POST /api/todos`
возвращает `201` и todo доступен по `GET /api/todos/{id}`, но отсутствует в выборках
`GET /api/todos` и QUERY — и челлендж, требующий его присутствия, не кредитуется.
Сбой воспроизводится и на «прогретой» сессии, поэтому `todo_factory` создаёт todo
с ретраем: до 3 попыток, каждая — отдельный шаг в Allure; после создания проверяется
видимость id в `GET /api/todos`, и в тестах, где созданный todo должен попасть в
выборку, дополнительно проверяется его присутствие в ответе фильтра/QUERY.

## Development


```bat
uv run ruff check .
uv run ruff format --check .
```

Конфигурация ruff: `line-length = 100`, формат — сохранение кавычек как в исходнике
(`quote-style = 'preserve'`, в проекте используются одинарные);
правила — `F, E, W, I, N, UP, B, C4, SIM, RET, PT, PTH, DTZ, T20, ARG, ERA, S,
PLE, PLW, RUF` с `per-file-ignores` для тестов (например, `S101`, `S105`, `S106`)
(см. `pyproject.toml`).

## CI

GitHub Actions (`.github/workflows/ci.yml`) запускается на push в `main` и на каждый
`pull_request`. Никаких секретов и `.env` не требуется: настройки берутся дефолтные
(`config.py`), каждый прогон работает со свежей throwaway-сессией challenger.

Три job'а:

- `checks` — быстрая обратная связь: `uv sync --frozen`, `ruff check`, `ruff format --check`
  и smoke-выборка `pytest -m smoke`.
- `full-suite` — полный регресс из 114 тестов против `https://apichallenges.com` с
  `--scoreboard`; запускается только после успешных `checks`. Артефакт `allure-results`
  выгружается всегда, даже при падении тестов.
- `allure-report` — генерация Allure-отчёта из артефакта и публикация на GitHub Pages
  (только для `main`).

Свежий push в ветку отменяет предыдущий запуск для неё (`concurrency.cancel-in-progress`).
Локально те же проверки: `uv run ruff check .`, `uv run ruff format --check .`,
`uv run pytest -m smoke -q`, `uv run pytest -q --scoreboard`.
