import pytest

from api_challenges.assertions import assert_content_type, assert_status_code, assert_todo_item
from api_challenges.clients import TODOS_PATH, ApiError


@pytest.mark.positive
@pytest.mark.smoke
def test_003_get_todos(api_client):
    response = api_client.get(TODOS_PATH)
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    payload = response.json()
    todos = payload['todos']
    for todo in todos:
        assert_todo_item(todo)

@pytest.mark.negative
@pytest.mark.regression
def test_004_get_todo_not_plural(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.get('/api/todo')
    assert exc.value.status_code == 404

@pytest.mark.positive
@pytest.mark.regression
def test_005_get_todo_by_id(api_client):
    response = api_client.get(TODOS_PATH)
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    payload = response.json()
    todos = payload['todos']
    assert todos, 'No todos in the session'
    assert_todo_item(todos[0])
    todo_id = todos[0]['id']
    response_with_id = api_client.get(f'{TODOS_PATH}/{todo_id}')
    assert_status_code(response=response_with_id, expected_status_code=200)
    assert_content_type(response=response_with_id,
                        expected_content_type='application/json')
    found = response_with_id.json()['todos'][0]
    assert_todo_item(found)
    assert found['id'] == todo_id, f'Wrong id returned: expected {todo_id!r}'

@pytest.mark.negative
@pytest.mark.regression
def test_006_get_todo_not_exist(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.get(f'{TODOS_PATH}/999999')
    assert exc.value.status_code == 404
