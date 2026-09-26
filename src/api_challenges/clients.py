import json
from typing import Any

import allure
import httpx

CHALLENGER_HEADER = 'X-CHALLENGER'
CHALLENGER_PATH = '/api/challenger'
CHALLENGES_PATH = '/api/challenges'
TODOS_PATH = '/api/todos'
HEARTBEAT_PATH = '/api/heartbeat'
SECRET_PATH = '/api/secret'
BASIC_AUTHORIZATION = 'Basic YWRtaW46cGFzc3dvcmQ='
_MASKED_HEADERS = {'authorization', 'x-auth-token'}
_MAX_BODY_CHARS = 50 * 1024


def _mask_secret_value(key: str, value: str) -> str:
    return '***' if key.lower() in _MASKED_HEADERS and value else value


def _mask_token_in_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: ('***' if k.lower() == 'token' and v else _mask_token_in_payload(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_mask_token_in_payload(item) for item in value]
    return value


def _format_body(body: bytes, content_type: str) -> str:
    text = body.decode('utf-8', errors='replace')
    if 'json' in content_type.lower():
        try:
            payload = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass
        else:
            text = json.dumps(_mask_token_in_payload(payload), indent=2, ensure_ascii=False)
    if len(text) > _MAX_BODY_CHARS:
        text = text[:_MAX_BODY_CHARS] + f'\n…[truncated {len(text) - _MAX_BODY_CHARS} bytes]'
    return text


def _attach_request(request: httpx.Request, method: str, path: str) -> None:
    headers = '\n'.join(f'{k}: {_mask_secret_value(k, v)}' for k, v in request.headers.items())
    body = _format_body(request.content, request.headers.get('content-type', ''))
    text = f'{method} {request.url}\n\n{headers}\n\n{body}'
    allure.attach(
        text, name=f'Request: {method} {path}', attachment_type=allure.attachment_type.TEXT
    )


def _attach_response(response: httpx.Response) -> None:
    headers = '\n'.join(f'{k}: {_mask_secret_value(k, v)}' for k, v in response.headers.items())
    body = _format_body(response.content, response.headers.get('content-type', ''))
    text = f'{response.status_code}\n\n{headers}\n\n{body}'
    allure.attach(
        text, name=f'Response: {response.status_code}', attachment_type=allure.attachment_type.TEXT
    )


class ApiError(RuntimeError):
    def __init__(self, method: str, url: str, status_code: int, body: str) -> None:
        self.method = method
        self.url = url
        self.status_code = status_code
        self.body = body
        super().__init__(f'{method} {url} -> {status_code}')


class BaseClient:
    def __init__(
        self, base_url: str, *, timeout: float = 15.0, headers: dict[str, str] | None = None
    ) -> None:
        default_headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        default_headers.update(headers or {})
        base_url = base_url.rstrip('/')
        self._headers = default_headers
        self._client = httpx.Client(
            base_url=base_url, headers=self._headers, timeout=timeout, follow_redirects=True
        )

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        headers = dict(self._headers)
        headers.update(kwargs.pop('headers', None) or {})
        response = self._client.request(method, path, headers=headers, **kwargs)
        with allure.step(f'{method} {path}'):
            _attach_request(response.request, method, path)
            _attach_response(response)
        value = response.headers.get(CHALLENGER_HEADER)
        if value:
            self._headers[CHALLENGER_HEADER] = value
        if response.is_error:
            raise ApiError(
                method=method,
                url=str(response.url),
                status_code=response.status_code,
                body=response.text,
            )
        return response

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request('GET', path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request('POST', path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request('PUT', path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request('PATCH', path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request('DELETE', path, **kwargs)

    def head(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request('HEAD', path, **kwargs)

    def options(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request('OPTIONS', path, **kwargs)

    def query(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request('QUERY', path, **kwargs)

    def trace(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request('TRACE', path, **kwargs)

    def create_challenger(self) -> str:
        self.post(CHALLENGER_PATH)
        guid = self.challenger
        if not guid:
            raise RuntimeError(f'POST {CHALLENGER_PATH} did not return {CHALLENGER_HEADER} header')
        return guid

    @property
    def challenger(self) -> str | None:
        return self._headers.get(CHALLENGER_HEADER)

    def use_challenger(self, guid: str) -> None:
        self._headers[CHALLENGER_HEADER] = guid

    def close(self) -> None:
        self._client.close()
