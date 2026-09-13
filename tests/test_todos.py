import pytest

from api_challenges.assertions import (
    assert_content_type,
    assert_status_code,
    assert_todo_item,
    assert_todo_item_matches,
)
from api_challenges.clients import TODOS_PATH, ApiError


@pytest.mark.positive
@pytest.mark.smoke
@pytest.mark.challenge(3)
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
@pytest.mark.challenge(4)
def test_004_get_todo_not_plural(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.get('/api/todo')
    assert exc.value.status_code == 404

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(5)
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
@pytest.mark.challenge(6)
def test_006_get_todo_not_exist(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.get(f'{TODOS_PATH}/999999')
    assert exc.value.status_code == 404

@pytest.mark.positive
@pytest.mark.smoke
@pytest.mark.challenge(23)
def test_007_create_minimal_body_todo(api_client):
    body = {'title': 'Test title'}
    response = api_client.post(TODOS_PATH, json=body)
    payload = response.json()
    new_id = payload['id']
    try:
        assert_status_code(response=response, expected_status_code=201)
        assert_content_type(response=response, expected_content_type='application/json')
        assert_todo_item(payload)
        assert_todo_item_matches(item=payload, expected=body)
        assert response.headers.get('Location') == f'{TODOS_PATH}/{new_id}', \
            f'Unexpected Location: {response.headers.get("Location")!r}'
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(23)
@pytest.mark.parametrize('case_info, title',[
    ('Кейс 08.01 - title = 1 cимвол','T'),
    ('Кейс 08.02 - title = 49 cимволов','t'*49),
    ('Кейс 08.03 - title = 50 cимволов','T'*50)
])
def test_008_create_full_body_todo(api_client, case_info, title):
    body = {'title': title, 'doneStatus': True, 'description': 'test description'}
    response = api_client.post(TODOS_PATH, json=body)
    payload = response.json()
    new_id = payload['id']
    try:
        assert_status_code(response=response, expected_status_code=201)
        assert_content_type(response=response, expected_content_type='application/json')
        assert_todo_item(payload)
        assert_todo_item_matches(item=payload, expected=body)
        assert response.headers.get('Location') == f'{TODOS_PATH}/{new_id}', \
            f'Unexpected Location: {response.headers.get("Location")!r}'
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(34)
def test_009_put_title_partial(api_client):
    post_body = {'title': 'Test title', 'doneStatus': True, 'description': 'test description'}
    response = api_client.post(TODOS_PATH, json=post_body)
    post_payload = response.json()
    new_id = post_payload['id']
    try:
        assert_status_code(response=response, expected_status_code=201)
        assert_content_type(response=response, expected_content_type='application/json')
        assert_todo_item(post_payload)
        assert_todo_item_matches(item=post_payload, expected=post_body)

        put_body = {'title': 'test updated title'}
        put_response = api_client.put(f'{TODOS_PATH}/{new_id}', json=put_body)
        put_payload = put_response.json()
        put_expected = {'title': put_body['title'], 'doneStatus': False, 'description': ''}
        assert_status_code(response=put_response, expected_status_code=200)
        assert_content_type(response=put_response, expected_content_type='application/json')
        assert_todo_item(put_payload)
        assert_todo_item_matches(item=put_payload, expected=put_expected)
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(45)
def test_010_patch_done_status(api_client):
    post_body = {'title': 'Test title', 'doneStatus': False, 'description': 'test description'}
    response = api_client.post(TODOS_PATH, json=post_body)
    post_payload = response.json()
    new_id = post_payload['id']
    try:
        assert_status_code(response=response, expected_status_code=201)
        assert_content_type(response=response, expected_content_type='application/json')
        assert_todo_item(post_payload)
        assert_todo_item_matches(item=post_payload, expected=post_body)

        patch_body = {'doneStatus': True}
        patch_response = api_client.patch(f'{TODOS_PATH}/{new_id}', json=patch_body)
        patch_payload = patch_response.json()
        patch_expected = {**post_payload, 'doneStatus': patch_body['doneStatus']}
        assert_status_code(response=patch_response, expected_status_code=200)
        assert_content_type(response=patch_response, expected_content_type='application/json')
        assert_todo_item(patch_payload)
        assert_todo_item_matches(item=patch_payload, expected=patch_expected)
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(41)
def test_011_delete_todo(api_client):
    post_body = {'title': 'Test title', 'doneStatus': False, 'description': 'test description'}
    response = api_client.post(TODOS_PATH, json=post_body)
    post_payload = response.json()
    new_id = post_payload['id']
    try:
        assert_status_code(response=response, expected_status_code=201)
        assert_content_type(response=response, expected_content_type='application/json')
        assert_todo_item(post_payload)
        assert_todo_item_matches(item=post_payload, expected=post_body)
    except Exception:
        api_client.delete(f'{TODOS_PATH}/{new_id}')
        raise

    delete_response = api_client.delete(f'{TODOS_PATH}/{new_id}')
    assert_status_code(response=delete_response, expected_status_code=204)

    with pytest.raises(ApiError) as exc:
        api_client.get(f'{TODOS_PATH}/{new_id}')
    assert exc.value.status_code == 404

@pytest.mark.negative
@pytest.mark.regression
def test_012_create_empty_body_todo(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.post(TODOS_PATH, json={})
    assert exc.value.status_code == 422

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(25)
def test_013_create_todo_too_long_title(api_client):
    body = {'title': 'T'*51, 'doneStatus': True, 'description': 'test description'}
    with pytest.raises(ApiError) as exc:
        api_client.post(TODOS_PATH, json=body)
    assert exc.value.status_code == 422

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(29)
def test_014_create_todo_id_in_body(api_client):
    body = {'id': 1, 'title': 'Test title', 'doneStatus': True, 'description': 'test description'}
    with pytest.raises(ApiError) as exc:
        api_client.post(TODOS_PATH, json=body)
    assert exc.value.status_code == 422

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(24)
def test_015_create_todo_string_done_status(api_client):
    body = {'title': 'Test title', 'doneStatus': 'True', 'description': 'test description'}
    with pytest.raises(ApiError) as exc:
        api_client.post(TODOS_PATH, json=body)
    assert exc.value.status_code == 422

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(39)
def test_016_put_not_found(api_client):
    body = {'title': 'Test title', 'doneStatus': True, 'description': 'test description'}
    with pytest.raises(ApiError) as exc:
        api_client.put(f'{TODOS_PATH}/9999999', json=body)
    assert exc.value.status_code == 404
