import fnmatch
import re

import pytest

from api_challenges.assertions import (
    assert_content_type,
    assert_status_code,
    assert_todo_item,
    assert_todo_item_matches,
)
from api_challenges.clients import TODOS_PATH


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(7)
def test_017_done_status_false(api_client):
    response = api_client.get(f'{TODOS_PATH}?doneStatus=false')
    payload = response.json()
    todos = payload['todos']
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    for todo in todos:
        assert_todo_item(todo)
        assert_todo_item_matches(item=todo, expected={'doneStatus': False})

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(7)
def test_018_done_status_true(api_client):
    body = {'title': 'Test title', 'doneStatus': True, 'description': 'test description'}
    post_response = api_client.post(TODOS_PATH, json=body)
    try:
        assert_status_code(response=post_response, expected_status_code=201)
        post_payload = post_response.json()
        new_id = post_payload['id']
        assert_content_type(response=post_response, expected_content_type='application/json')
        assert_todo_item(post_payload)
        assert_todo_item_matches(item=post_payload, expected=body)

        get_response = api_client.get(f'{TODOS_PATH}?doneStatus=true')
        assert_status_code(response=get_response, expected_status_code=200)
        get_payload = get_response.json()
        todos = get_payload['todos']
        assert post_payload['id'] in {t['id'] for t in todos}, \
            'Filter did not include the created doneStatus=true todo'
        assert_content_type(response=get_response, expected_content_type='application/json')
        for todo in todos:
            assert_todo_item(todo)
            assert_todo_item_matches(item=todo, expected={'doneStatus': True})
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(8)
@pytest.mark.parametrize('case_info, id',[
    ('Кейс 19.01 - id > 1', 1),
    ('Кейс 19.02 - id > 3', 3)
])
def test_019_id_greater_than(api_client, case_info, id):
    response = api_client.get(f'{TODOS_PATH}?id>{id}')
    assert_status_code(response=response, expected_status_code=200)
    payload = response.json()
    todos = payload['todos']
    assert_content_type(response=response, expected_content_type='application/json')
    for todo in todos:
        assert_todo_item(todo)
        assert todo['id'] > id, f'Incorrect id in response: {todo['id']}, id should be > {id}'

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(9)
@pytest.mark.parametrize('case_info, id',[
    ('Кейс 20.01 - id < 1', 1),
    ('Кейс 20.02 - id < 3', 3)
])
def test_020_id_less_than(api_client, case_info, id):
    response = api_client.get(f'{TODOS_PATH}?id<{id}')
    assert_status_code(response=response, expected_status_code=200)
    payload = response.json()
    todos = payload['todos']
    assert_content_type(response=response, expected_content_type='application/json')
    for todo in todos:
        assert_todo_item(todo)
        assert todo['id'] < id, f'Incorrect id in response: {todo['id']}, id should be < {id}'

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(10)
@pytest.mark.parametrize('case_info, id',[
    ('Кейс 21.01 - id = 2', 2),
    ('Кейс 21.02 - id = 4', 4)
])
def test_021_id_equal_filter_id(api_client, case_info, id):
    response = api_client.get(f'{TODOS_PATH}?id={id}')
    assert_status_code(response=response, expected_status_code=200)
    payload = response.json()
    todos = payload['todos']
    assert_content_type(response=response, expected_content_type='application/json')
    assert len(todos) == 1, 'Response contains more than 1 todo'
    for todo in todos:
        assert_todo_item(todo)
        assert todo['id'] == id, f'Incorrect id in response: {todo['id']}, id should be = {id}'

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(11)
@pytest.mark.parametrize('case_info, description, regexp',[
    ('Кейс 22.01 - regexp = [A-Za-z]{4} [a-z]{4} [a-z]{3} [a-z]{6} [0-9]{2}.[0-9]{2}',
     'Test text for filter 22.01',
     r'[A-Za-z]{4} [a-z]{4} [a-z]{3} [a-z]{6} [0-9]{2}.[0-9]{2}'),
    ('Кейс 22.02 - regexp = .*regex.*', 'Test description regexp 22.02', r'.*regex.*')
])
def test_022_description_regexp(api_client, case_info, description, regexp):
    test_regexp = re.compile(regexp)
    body = {'title': 'Test title', 'doneStatus': True, 'description': description}
    post_response = api_client.post(TODOS_PATH, json=body)
    post_payload = post_response.json()
    new_id = post_payload['id']
    try:
        assert_status_code(response=post_response, expected_status_code=201)
        assert_content_type(response=post_response, expected_content_type='application/json')
        assert_todo_item(post_payload)
        assert_todo_item_matches(item=post_payload, expected=body)

        get_response = api_client.get(f'{TODOS_PATH}?description~={regexp}')
        assert_status_code(response=get_response, expected_status_code=200)
        get_payload = get_response.json()
        todos = get_payload['todos']
        assert_content_type(response=get_response, expected_content_type='application/json')
        assert post_payload['description'] in {t['description'] for t in todos}, \
            f'Filter did not include the created description = {description} todo'
        for todo in todos:
            assert_todo_item(todo)
            assert test_regexp.fullmatch(todo['description']), \
            f'Incorrect description format: {todo['description']}'
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(12)
@pytest.mark.parametrize('case_info, description, wildcard',[
    ('Кейс 23.01 - wildcard = Test*01', 'Test text for filter 23.01',
     'Test*01'),
    ('Кейс 23.02 - wildcard = *wildcard*', 'Test description wildcard 23.02', '*wildcard*')
])
def test_023_description_wildcard(api_client, case_info, description, wildcard):
    body = {'title': 'Test title', 'doneStatus': True, 'description': description}
    post_response = api_client.post(TODOS_PATH, json=body)
    post_payload = post_response.json()
    new_id = post_payload['id']
    try:
        assert_status_code(response=post_response, expected_status_code=201)
        assert_content_type(response=post_response, expected_content_type='application/json')
        assert_todo_item(post_payload)
        assert_todo_item_matches(item=post_payload, expected=body)

        get_response = api_client.get(f'{TODOS_PATH}?description*={wildcard}')
        assert_status_code(response=get_response, expected_status_code=200)
        get_payload = get_response.json()
        todos = get_payload['todos']
        assert_content_type(response=get_response, expected_content_type='application/json')
        assert post_payload['description'] in {t['description'] for t in todos}, \
            f'Filter did not include the created description = {description} todo'
        for todo in todos:
            assert_todo_item(todo)
            assert fnmatch.fnmatchcase(todo['description'], wildcard), \
            f'Incorrect description: {todo['description']}, should contain: {wildcard}'
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')
