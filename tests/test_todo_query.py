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
@pytest.mark.challenge(42)
@pytest.mark.parametrize(
    ('_case_info', 'done_status'),
    [('Кейс 46.1 - doneStatus = true', True), ('Кейс 46.2 - doneStatus = false', False)],
)
def test_046_query_done_status(api_client, _case_info, done_status, todo_factory):
    create_body = {'title': 'test title', 'doneStatus': True, 'description': 'test description'}
    create_response, create_payload = todo_factory(json=create_body)
    assert_content_type(response=create_response, expected_content_type='application/json')
    assert_todo_item(create_payload)
    assert_todo_item_matches(item=create_payload, expected=create_body)

    response = api_client.query(
        TODOS_PATH,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        content=f'doneStatus={done_status}',
    )
    query_payload = response.json()
    todos = query_payload['todos']
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    for todo in todos:
        assert_todo_item(todo)
        assert todo['doneStatus'] is done_status, (
            f'Incorrect doneStatus: {todo['doneStatus']}, should be: {done_status}'
        )


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(43)
@pytest.mark.parametrize(
    ('_case_info', 'done_status'),
    [('Кейс 47.1 - doneStatus = true', 'true'), ('Кейс 47.2 - doneStatus = false', 'false')],
)
def test_047_query_done_status_jsonpath(api_client, _case_info, done_status, todo_factory):
    create_body = {'title': 'test title', 'doneStatus': True, 'description': 'test description'}
    create_response, create_payload = todo_factory(json=create_body)
    assert_content_type(response=create_response, expected_content_type='application/json')
    assert_todo_item(create_payload)
    assert_todo_item_matches(item=create_payload, expected=create_body)

    response = api_client.query(
        TODOS_PATH,
        headers={'Content-Type': 'application/jsonpath'},
        content=f'$.todos[?(@.doneStatus == {done_status})]',
    )
    query_payload = response.json()
    todos = query_payload['todos']
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    for todo in todos:
        assert_todo_item(todo)
        assert str(todo['doneStatus']).lower() == done_status, (
            f'Incorrect doneStatus: {str(todo['doneStatus']).lower()}, should be: {done_status}'
        )


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(44)
@pytest.mark.parametrize(
    ('_case_info', 'done_status'),
    [('Кейс 48.1 - doneStatus = true', True), ('Кейс 48.2 - doneStatus = false', False)],
)
def test_048_query_done_status_json(api_client, _case_info, done_status, todo_factory):
    query_body = {'filter': {'doneStatus': done_status}}
    create_body = {'title': 'test title', 'doneStatus': True, 'description': 'test description'}
    create_response, create_payload = todo_factory(json=create_body)
    assert_content_type(response=create_response, expected_content_type='application/json')
    assert_todo_item(create_payload)
    assert_todo_item_matches(item=create_payload, expected=create_body)
    response = api_client.query(
        TODOS_PATH,
        headers={'Content-Type': 'application/vnd.thingifier.query+json'},
        json=query_body,
    )
    query_payload = response.json()
    todos = query_payload['todos']
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    for todo in todos:
        assert_todo_item(todo)
        assert todo['doneStatus'] is done_status, (
            f'Incorrect doneStatus: {todo['doneStatus']}, should be: {done_status}'
        )
