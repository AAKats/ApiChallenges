from typing import Any

import httpx

CHALLENGER_HEADER = 'X-CHALLENGER'
CHALLENGER_PATH = '/api/challenger'
CHALLENGES_PATH = '/api/challenges'
TODOS_PATH = '/api/todos'
HEARTBEAT_PATH = '/api/heartbeat'

class ApiError(RuntimeError):
    def __init__(self, method: str, url: str, status_code: int, body: str) -> None:
        self.method = method
        self.url = url
        self.status_code = status_code
        self.body = body
        super().__init__(f'{method} {url} -> {status_code}')

class BaseClient:
    def __init__(
            self,
            base_url: str,
            *,
            timeout: float = 15.0,
            headers: dict[str, str] | None = None
    ) -> None:
        default_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        default_headers.update(headers or {})
        base_url = base_url.rstrip('/')
        self._headers = default_headers
        self._client = httpx.Client(
            base_url=base_url,
            headers=self._headers,
            timeout=timeout,
            follow_redirects=True
        )
    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        headers = dict(self._headers)
        headers.update(kwargs.pop('headers', None) or {})
        response = self._client.request(method, path, headers=headers, **kwargs)
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
            raise RuntimeError(
                f'POST {CHALLENGER_PATH} did not return {CHALLENGER_HEADER} header'
            )
        return guid

    @property
    def challenger(self) -> str | None:
        return self._headers.get(CHALLENGER_HEADER)

    def use_challenger(self, guid: str) -> None:
        self._headers[CHALLENGER_HEADER] = guid

    def close(self) -> None:
        self._client.close()




