import re

import httpx

from api_challenges.utils import todo_from_xml


def assert_valid_guid(guid: str) -> None:
    guid_re = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}')
    if not guid_re.fullmatch(guid):
        raise AssertionError(f'Incorrect GUID format: {guid!r}')


def assert_status_code(*, response: httpx.Response, expected_status_code: int) -> None:
    status_code = response.status_code
    if status_code != expected_status_code:
        raise AssertionError(f'Incorrect status code {status_code},'
                             f' should be {expected_status_code}')


def assert_error_status_code(*, received_status_code: int, expected_status_code: int) -> None:
    if received_status_code != expected_status_code:
        raise AssertionError(f'Incorrect status code {received_status_code},'
                             f' should be {expected_status_code}')


def assert_content_type(*, response: httpx.Response, expected_content_type: str) -> None:
    content_type = response.headers.get('Content-Type')
    if content_type != expected_content_type:
        raise AssertionError(f'Incorrect content type {content_type},'
                             f' should be {expected_content_type}')


def assert_challenge_item(item: dict) -> None:
    assert isinstance(item, dict), f'not a dict: {item!r}'
    assert isinstance(item.get('id'), int), f'id missing or not int: {item.get('id')!r}'
    assert isinstance(item.get('name'), str), f'name missing or not str: {item.get('name')!r}'
    assert isinstance(item.get('status'), bool), \
        f'status missing or not bool: {item.get('status')!r}'


def assert_todo_item(item: dict) -> None:
    assert isinstance(item, dict), f'not a dict: {item!r}'
    assert isinstance(item.get('id'), int), f'id missing or not int: {item.get('id')!r}'
    assert isinstance(item.get('title'), str), f'title missing or not str: {item.get('title')!r}'
    assert isinstance(item.get('doneStatus'), bool), \
        f'done status missing or not bool: {item.get('doneStatus')!r}'
    assert isinstance(item.get('description'), str), \
        f'description missing or not str: {item.get('description')!r}'

def assert_todo_item_matches(*, item: dict, expected: dict) -> None:
    for field, expected_value in expected.items():
        if field not in item or item[field] != expected_value:
            raise AssertionError(
                f'todo field {field!r} mismatch: expected {expected_value!r}, '
                f'got {item.get(field)!r}'
            )

def assert_sorted(items, sort_by):
    fields = []
    for part in sort_by.split(','):
        part = part.strip()
        desc = part.startswith('-')
        fields.append((part.lstrip('+-'), desc))
    for left, right in zip(items, items[1:]):
        for field, desc in fields:
            left_val, right_val = left[field], right[field]
            if left_val == right_val:
                continue
            if desc:
                assert left_val > right_val, f'Incorrect order for {field} desc'
            else:
                assert left_val < right_val, f'Incorrect order for {field} asc'
            break

def assert_error_message(item, *, error_message):
    response_error_message = item['errorMessages'][0]
    assert response_error_message == error_message, \
        f'Incorrect error message: {response_error_message}, should be: {error_message}'

def assert_todo_item_xml(item: str) -> None:
    assert_todo_item(todo_from_xml(item))

def assert_todo_item_matches_xml(*, item: str, expected: dict) -> None:
    assert_todo_item_matches(item=todo_from_xml(item), expected=expected)

def assert_todo_item_for_user_in_db(item: dict) -> None:
    assert isinstance(item, dict), f'not a dict: {item!r}'
    assert isinstance(item.get('id'), int), f'id missing or not int: {item.get('id')!r}'
    assert isinstance(item.get('title'), str), f'title missing or not str: {item.get('title')!r}'

def assert_note_item(item: dict) -> None:
    assert isinstance(item, dict), f'not a dict: {item!r}'
    assert isinstance(item.get('note'), str), f'note missing or not str: {item.get('note')!r}'


def assert_note_item_matches(*, item: dict, expected: dict) -> None:
    for field, expected_value in expected.items():
        if field not in item or item[field] != expected_value:
            raise AssertionError(
                f'note field {field!r} mismatch: expected {expected_value!r}, '
                f'got {item.get(field)!r}'
            )