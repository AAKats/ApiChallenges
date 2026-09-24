import json

import pytest

from api_challenges.assertions import (
    assert_content_type,
    assert_error_message,
    assert_status_code,
    assert_todo_item_for_user_in_db,
)
from api_challenges.clients import CHALLENGER_HEADER, CHALLENGER_PATH, ApiError
from api_challenges.utils import generate_guid


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(70)
def test_070_get_challenger_progress(api_client):
    guid = api_client.challenger
    response = api_client.get(f'{CHALLENGER_PATH}/{guid}',
                              headers={'Accept': 'application/json', CHALLENGER_HEADER: guid})
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    payload = response.json()
    assert payload['xChallenger'] == guid, \
        f'Incorrect challenger guid: {payload['xChallenger']}, should be: {guid}'

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(71)
def test_071_restore_progress(api_client):
    guid = api_client.challenger
    response = api_client.post(CHALLENGER_PATH,
                               headers={'Accept': 'application/json',
                                        CHALLENGER_HEADER: guid})
    assert_status_code(response=response, expected_status_code=200)
    assert response.text == '', f'Unexpected restore body: {response.text!r}'

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(72)
def test_072_get_progress(api_client):
    guid = api_client.challenger
    get_response = api_client.get(f'{CHALLENGER_PATH}/{guid}', headers={
        'Accept': 'application/json',
        CHALLENGER_HEADER: guid
    })
    assert_status_code(response=get_response, expected_status_code=200)
    assert_content_type(response=get_response, expected_content_type='application/json')
    get_payload = get_response.json()
    assert get_payload['xChallenger'] == guid, \
        f'Incorrect challenger guid: {get_payload['xChallenger']}, should be: {guid}'

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(73)
def test_073_restore_challenger_progress(api_client):
    guid = api_client.challenger
    get_response = api_client.get(f'{CHALLENGER_PATH}/{guid}', headers={
        'Accept': 'application/json',
        CHALLENGER_HEADER: guid
    })
    assert_status_code(response=get_response, expected_status_code=200)
    assert_content_type(response=get_response, expected_content_type='application/json')
    payload = get_response.json()
    assert payload['xChallenger'] == guid, \
        f'Incorrect challenger guid: {payload['xChallenger']}, should be: {guid}'
    put_response = api_client.put(f'{CHALLENGER_PATH}/{guid}', headers={
        'Accept': 'application/json',
        CHALLENGER_HEADER: guid
    }, json=payload)
    assert_status_code(response=put_response, expected_status_code=200)
    assert_content_type(response=put_response, expected_content_type='application/json')
    payload = put_response.json()
    assert payload['xChallenger'] == guid, \
        f'Incorrect challenger guid: {payload['xChallenger']}, should be: {guid}'

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(74)
def test_074_mismatch_guid(api_client):
    guid = api_client.challenger
    new_guid = generate_guid()
    get_response = api_client.get(f'{CHALLENGER_PATH}/{guid}', headers={
        'Accept': 'application/json',
        CHALLENGER_HEADER: guid
    })
    assert_status_code(response=get_response, expected_status_code=200)
    assert_content_type(response=get_response, expected_content_type='application/json')
    payload = get_response.json()
    assert payload['xChallenger'] == guid, \
        f'Incorrect challenger new_guid: {payload['xChallenger']}, should be: {guid}'
    with pytest.raises(ApiError) as exc:
        api_client.put(f'{CHALLENGER_PATH}/{new_guid}', headers={
            'Accept': 'application/json',
            CHALLENGER_HEADER: guid
        }, json=payload)
    assert exc.value.status_code == 409
    assert_error_message(json.loads(exc.value.body),
                     error_message='URL GUID does not match payload X-CHALLENGER')

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(75)
def test_075_create_guid(api_client):
    guid = api_client.challenger
    new_guid = generate_guid()
    get_response = api_client.get(f'{CHALLENGER_PATH}/{guid}', headers={
        'Accept': 'application/json',
        CHALLENGER_HEADER: guid
    })
    assert_status_code(response=get_response, expected_status_code=200)
    assert_content_type(response=get_response, expected_content_type='application/json')
    get_payload = get_response.json()
    assert get_payload['xChallenger'] == guid, \
        f'Incorrect challenger guid: {get_payload['xChallenger']}, should be: {guid}'
    create_payload = get_payload.copy()
    create_payload['xChallenger'] = new_guid

    put_response = api_client.put(f'{CHALLENGER_PATH}/{new_guid}', headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        CHALLENGER_HEADER: guid
    }, json=create_payload)
    assert_status_code(response=put_response, expected_status_code=201)
    api_client.use_challenger(guid)
    assert_content_type(response=put_response, expected_content_type='application/json')

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(76)
def test_076_current_todos_database(api_client):
    guid = api_client.challenger
    get_response = api_client.get(f'{CHALLENGER_PATH}/database/{guid}', headers={
        'Accept': 'application/json',
        CHALLENGER_HEADER: guid
    })
    assert_status_code(response=get_response, expected_status_code=200)
    assert_content_type(response=get_response, expected_content_type='application/json')
    get_payload = get_response.json()
    todos = get_payload['todos']
    for todo in todos:
        assert_todo_item_for_user_in_db(todo)

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(77)
def test_077_update_todos_database(api_client):
    guid = api_client.challenger
    get_response = api_client.get(f'{CHALLENGER_PATH}/database/{guid}', headers={
        'Accept': 'application/json',
        CHALLENGER_HEADER: guid
    })
    assert_status_code(response=get_response, expected_status_code=200)
    assert_content_type(response=get_response, expected_content_type='application/json')
    get_payload = get_response.json()
    todos = get_payload['todos']
    for todo in todos:
        assert_todo_item_for_user_in_db(todo)
    new_todo = {
        'id': max(todo['id'] for todo in todos)+1,
        'title': 'New todo',
        'description': 'New todo description'
    }
    get_payload['todos'].append(new_todo)
    put_response = api_client.put(f'{CHALLENGER_PATH}/database/{guid}', headers={
        'Accept': 'application/json',
        CHALLENGER_HEADER: guid
    }, json= get_payload)
    assert_status_code(response=put_response, expected_status_code=204)