import json

import pytest

from api_challenges.assertions import (
    assert_content_type,
    assert_error_message,
    assert_error_status_code,
    assert_status_code,
    assert_todo_item,
    assert_todo_item_matches,
    assert_todo_item_matches_xml,
    assert_todo_item_xml,
)
from api_challenges.clients import TODOS_PATH, ApiError
from api_challenges.utils import (
    request_todo_from_xml,
    todo_from_xml,
    todos_from_csv,
    todos_from_html,
    todos_from_tsv,
    todos_from_xml,
)


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
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=404)
    assert_error_message(json.loads(exc.value.body), error_message='404 resource Unknown')


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
    assert_content_type(response=response_with_id, expected_content_type='application/json')
    found = response_with_id.json()['todos'][0]
    assert_todo_item(found)
    assert found['id'] == todo_id, f'Wrong id returned: expected {todo_id!r}'


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(6)
def test_006_get_todo_not_exist(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.get(f'{TODOS_PATH}/999999')
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=404)
    assert_error_message(
        json.loads(exc.value.body), error_message='Could not find an instance with todos/999999'
    )


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
        assert response.headers.get('Location') == f'{TODOS_PATH}/{new_id}', (
            f'Unexpected Location: {response.headers.get('Location')!r}'
        )
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(23)
@pytest.mark.parametrize(
    ('_case_info', 'title'),
    [
        ('Кейс 08.01 - title = 1 symbol', 'T'),
        ('Кейс 08.02 - title = 49 symbols', 't' * 49),
        ('Кейс 08.03 - title = 50 symbols', 'T' * 50),
    ],
)
def test_008_create_full_body_todo(api_client, _case_info, title):
    body = {'title': title, 'doneStatus': True, 'description': 'test description'}
    response = api_client.post(TODOS_PATH, json=body)
    payload = response.json()
    new_id = payload['id']
    try:
        assert_status_code(response=response, expected_status_code=201)
        assert_content_type(response=response, expected_content_type='application/json')
        assert_todo_item(payload)
        assert_todo_item_matches(item=payload, expected=body)
        assert response.headers.get('Location') == f'{TODOS_PATH}/{new_id}', (
            f'Unexpected Location: {response.headers.get('Location')!r}'
        )
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
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=404)
    assert_error_message(
        json.loads(exc.value.body), error_message=f'Could not find an instance with todos/{new_id}'
    )


@pytest.mark.negative
@pytest.mark.regression
def test_012_create_empty_body_todo(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.post(TODOS_PATH, json={})
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=422)
    assert_error_message(json.loads(exc.value.body), error_message='title : field is mandatory')


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(25)
def test_013_create_todo_too_long_title(api_client):
    body = {'title': 'T' * 51, 'doneStatus': True, 'description': 'test description'}
    with pytest.raises(ApiError) as exc:
        api_client.post(TODOS_PATH, json=body)
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=422)
    assert_error_message(
        json.loads(exc.value.body),
        error_message='Failed Validation: Maximum allowable length exceeded for '
        'title - maximum allowed is 50',
    )


@pytest.mark.negative
@pytest.mark.regression
def test_014_create_todo_id_in_body(api_client):
    body = {'id': 1, 'title': 'Test title', 'doneStatus': True, 'description': 'test description'}
    with pytest.raises(ApiError) as exc:
        api_client.post(TODOS_PATH, json=body)
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=422)
    assert_error_message(
        json.loads(exc.value.body),
        error_message='Failed Validation: Invalid Creation: Not allowed to create with id',
    )


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(24)
def test_015_create_todo_string_done_status(api_client):
    body = {'title': 'Test title', 'doneStatus': 'True', 'description': 'test description'}
    with pytest.raises(ApiError) as exc:
        api_client.post(TODOS_PATH, json=body)
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=422)


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(39)
def test_016_put_not_found(api_client):
    body = {'title': 'Test title', 'doneStatus': True, 'description': 'test description'}
    with pytest.raises(ApiError) as exc:
        api_client.put(f'{TODOS_PATH}/9999999', json=body)
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=404)


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(22)
def test_033_head_request(api_client):
    response = api_client.head(TODOS_PATH)
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    assert response.content == b''


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(26)
def test_034_too_long_description(api_client):
    body = {
        'title': 'description too long',
        'doneStatus': True,
        'description': '*3*5*7*10*13*16*19*22*25*28*31*34*37*40*43*46*49*52*55*58*61*64*67*70*73*76'
        '*79*82*85*88*91*94*97*101*105*109*113*117*121*125*129*133*137*141*145*149*'
        '153*157*161*165*169*173*177*181*185*189*193*197*201*',
    }
    with pytest.raises(ApiError) as exc:
        api_client.post(TODOS_PATH, json=body)
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=422)
    assert_error_message(
        json.loads(exc.value.body),
        error_message='Failed Validation: Maximum allowable length exceeded for '
        'description - maximum allowed is 200',
    )


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(27)
def test_035_max_out_content(api_client):
    body = {
        'title': '2*4*6*8*11*14*17*20*23*26*29*32*35*38*41*44*47*50*',
        'doneStatus': True,
        'description': '*3*5*7*9*12*15*18*21*24*27*30*33*36*39*42*45*48*51*54*57*60*63*66*69*72*75*'
        '78*81*84*87*90*93*96*100*104*108*112*116*120*124*128*132*136*140*144*148*'
        '152*156*160*164*168*172*176*180*184*188*192*196*200*',
    }
    response = api_client.post(TODOS_PATH, json=body)
    post_payload = response.json()
    new_id = post_payload['id']
    try:
        assert_status_code(response=response, expected_status_code=201)
        assert_content_type(response=response, expected_content_type='application/json')
        assert_todo_item(post_payload)
        assert_todo_item_matches(item=post_payload, expected=body)
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(28)
def test_036_content_too_long(api_client):
    body = {'title': 'too much content', 'doneStatus': True, 'description': 'D' * 5001}
    with pytest.raises(ApiError) as exc:
        api_client.post(TODOS_PATH, json=body)
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=413)
    assert_error_message(
        json.loads(exc.value.body),
        error_message='Error: request body too large, max allowed is 5000 bytes',
    )


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(29)
def test_037_extra_field(api_client):
    body = {
        'title': 'extra field',
        'doneStatus': True,
        'description': 'Test description',
        'priority': 'high',
    }
    with pytest.raises(ApiError) as exc:
        api_client.post(TODOS_PATH, json=body)
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=422)
    assert_error_message(
        json.loads(exc.value.body),
        error_message='Failed Validation: Could not find field: priority',
    )


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(30)
def test_038_put_to_create(api_client):
    body = {
        'id': 9999,
        'title': 'Test title',
        'doneStatus': True,
        'description': 'Test description',
    }
    with pytest.raises(ApiError) as exc:
        api_client.put(f'{TODOS_PATH}/9999', json=body)
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=422)
    assert_error_message(
        json.loads(exc.value.body),
        error_message='Cannot create todo with PUT due to Auto fields id',
    )


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(31)
def test_039_update_via_post(api_client):
    create_body = {'title': 'test title', 'doneStatus': False, 'description': 'test description'}
    updated_body = {
        'title': 'solution widget todo',
        'doneStatus': True,
        'description': 'created from the solution page',
    }
    create_response = api_client.post(TODOS_PATH, json=create_body)
    create_payload = create_response.json()
    new_id = create_payload['id']
    try:
        assert_status_code(response=create_response, expected_status_code=201)
        assert_content_type(response=create_response, expected_content_type='application/json')
        assert_todo_item(create_payload)
        assert_todo_item_matches(item=create_payload, expected=create_body)

        response = api_client.post(f'{TODOS_PATH}/{new_id}', json=updated_body)
        post_payload = response.json()
        assert_status_code(response=response, expected_status_code=200)
        assert_content_type(response=response, expected_content_type='application/json')
        assert_todo_item(post_payload)
        assert_todo_item_matches(item=post_payload, expected=updated_body)
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(32)
def test_040_update_via_post_not_exist(api_client):
    body = {
        'title': 'solution widget todo',
        'doneStatus': True,
        'description': 'created from the solution page',
    }
    with pytest.raises(ApiError) as exc:
        api_client.post(f'{TODOS_PATH}/9999', json=body)
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=404)
    assert_error_message(
        json.loads(exc.value.body),
        error_message='No such todo entity instance with id == 9999 found',
    )


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(33)
def test_041_update_via_put_full(api_client):
    create_body = {'title': 'test title', 'doneStatus': False, 'description': 'test description'}
    create_response = api_client.post(TODOS_PATH, json=create_body)
    create_payload = create_response.json()
    new_id = create_payload['id']
    try:
        assert_status_code(response=create_response, expected_status_code=201)
        assert_content_type(response=create_response, expected_content_type='application/json')
        assert_todo_item(create_payload)
        assert_todo_item_matches(item=create_payload, expected=create_body)
        updated_body = {
            'id': new_id,
            'title': 'full update widget todo',
            'doneStatus': True,
            'description': 'created from the solution page',
        }

        put_response = api_client.put(f'{TODOS_PATH}/{new_id}', json=updated_body)
        put_payload = put_response.json()
        assert_status_code(response=put_response, expected_status_code=200)
        assert_content_type(response=put_response, expected_content_type='application/json')
        assert_todo_item(put_payload)
        assert_todo_item_matches(item=put_payload, expected=updated_body)
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(35)
def test_042_update_via_put_body_id(api_client):
    create_body = {'title': 'test title', 'doneStatus': False, 'description': 'test description'}
    create_response = api_client.post(TODOS_PATH, json=create_body)
    create_payload = create_response.json()
    new_id = create_payload['id']
    try:
        assert_status_code(response=create_response, expected_status_code=201)
        assert_content_type(response=create_response, expected_content_type='application/json')
        assert_todo_item(create_payload)
        assert_todo_item_matches(item=create_payload, expected=create_body)
        updated_body = {
            'id': new_id,
            'title': 'full update widget todo',
            'doneStatus': True,
            'description': 'created from the solution page',
        }

        put_response = api_client.put(TODOS_PATH, json=updated_body)
        put_payload = put_response.json()
        assert_status_code(response=put_response, expected_status_code=200)
        assert_content_type(response=put_response, expected_content_type='application/json')
        assert_todo_item(put_payload)
        assert_todo_item_matches(item=put_payload, expected=updated_body)
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(37)
def test_043_update_via_put_no_title(api_client):
    body = {'doneStatus': True, 'description': 'created from the solution page'}
    with pytest.raises(ApiError) as exc:
        api_client.put(f'{TODOS_PATH}/10', json=body)
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=422)
    assert_error_message(
        json.loads(exc.value.body), error_message='Failed Validation: title : field is mandatory'
    )


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(38)
def test_044_update_via_put_no_id(api_client):
    body = {
        'title': 'update widget todo without id',
        'doneStatus': True,
        'description': 'created from the solution page',
    }
    with pytest.raises(ApiError) as exc:
        api_client.put(TODOS_PATH, json=body)
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=422)
    assert_error_message(
        json.loads(exc.value.body), error_message='PUT requires an identifier in the URI or payload'
    )


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(40)
def test_045_update_via_put_amend_id(api_client):
    body = {
        'id': 9999,
        'title': 'update widget todo without id',
        'doneStatus': True,
        'description': 'created from the solution page',
    }
    with pytest.raises(ApiError) as exc:
        api_client.put(f'{TODOS_PATH}/3', json=body)
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=422)
    assert_error_message(
        json.loads(exc.value.body), error_message='Can not amend id from 3 to 9999'
    )


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(46)
def test_049_merge_patch(api_client):
    post_body = {'title': 'Test title', 'doneStatus': False, 'description': 'test description'}
    response = api_client.post(TODOS_PATH, json=post_body)
    post_payload = response.json()
    new_id = post_payload['id']
    try:
        assert_status_code(response=response, expected_status_code=201)
        assert_content_type(response=response, expected_content_type='application/json')
        assert_todo_item(post_payload)
        assert_todo_item_matches(item=post_payload, expected=post_body)

        patch_body = {'description': 'patched with merge patch'}
        patch_response = api_client.patch(
            f'{TODOS_PATH}/{new_id}',
            headers={'Content-Type': 'application/merge-patch+json'},
            json=patch_body,
        )
        patch_payload = patch_response.json()
        patch_expected = {**post_payload, 'description': 'patched with merge patch'}
        assert_status_code(response=patch_response, expected_status_code=200)
        assert_content_type(response=patch_response, expected_content_type='application/json')
        assert_todo_item(patch_payload)
        assert_todo_item_matches(item=patch_payload, expected=patch_expected)
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(47)
def test_050_json_patch(api_client):
    post_body = {'title': 'Test title', 'doneStatus': False, 'description': 'test description'}
    response = api_client.post(TODOS_PATH, json=post_body)
    post_payload = response.json()
    new_id = post_payload['id']
    try:
        assert_status_code(response=response, expected_status_code=201)
        assert_content_type(response=response, expected_content_type='application/json')
        assert_todo_item(post_payload)
        assert_todo_item_matches(item=post_payload, expected=post_body)

        patch_body = [{'op': 'replace', 'path': '/title', 'value': 'patched with json patch'}]
        patch_response = api_client.patch(
            f'{TODOS_PATH}/{new_id}',
            headers={'Content-Type': 'application/json-patch+json'},
            json=patch_body,
        )
        patch_payload = patch_response.json()
        patch_expected = {**post_payload, 'title': 'patched with json patch'}
        assert_status_code(response=patch_response, expected_status_code=200)
        assert_content_type(response=patch_response, expected_content_type='application/json')
        assert_todo_item(patch_payload)
        assert_todo_item_matches(item=patch_payload, expected=patch_expected)
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(48)
def test_051_options(api_client):
    response = api_client.options(TODOS_PATH)
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='text/plain')
    assert response.content == b''


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(49)
def test_052_get_todos_xml(api_client):
    response = api_client.get(TODOS_PATH, headers={'Accept': 'application/xml'})
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/xml')
    for todo in todos_from_xml(response.text):
        assert_todo_item(todo)


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(51)
def test_053_get_todos_any(api_client):
    response = api_client.get(TODOS_PATH, headers={'Accept': '*/*'})
    payload = response.json()
    todos = payload['todos']
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    for todo in todos:
        assert_todo_item(todo)


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(53)
def test_054_get_todos_no_accept(api_client):
    response = api_client.get(TODOS_PATH, headers={'Accept': ''})
    payload = response.json()
    todos = payload['todos']
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    for todo in todos:
        assert_todo_item(todo)


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(54)
def test_055_get_todos_no_acceptable(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.get(TODOS_PATH, headers={'Accept': 'application/gzip'})
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=406)
    assert_error_message(json.loads(exc.value.body), error_message='Unrecognised Accept Type')


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(55)
@pytest.mark.parametrize(
    ('_case_info', 'done_status', 'expected_status'),
    [
        ('Кейс 56.1 - doneStatus = false', False, 'NEEDS-ACTION'),
        ('Кейс 56.2 - doneStatus = true', True, 'COMPLETED'),
    ],
)
def test_056_get_todo_calendar(api_client, _case_info, done_status, expected_status):
    create_body = {
        'title': 'calendar',
        'doneStatus': done_status,
        'description': 'test description',
    }
    create_response = api_client.post(TODOS_PATH, json=create_body)
    create_payload = create_response.json()
    new_id = create_payload['id']
    try:
        assert_status_code(response=create_response, expected_status_code=201)
        assert_content_type(response=create_response, expected_content_type='application/json')
        assert_todo_item(create_payload)
        assert_todo_item_matches(item=create_payload, expected=create_body)

        calendar_response = api_client.get(
            f'{TODOS_PATH}/{new_id}', headers={'Accept': 'text/calendar'}
        )
        assert_status_code(response=calendar_response, expected_status_code=200)
        assert_content_type(response=calendar_response, expected_content_type='text/calendar')
        lines = calendar_response.text.split('\r\n')
        assert lines[0] == 'BEGIN:VCALENDAR'
        assert lines[-1] == 'END:VCALENDAR'
        for key, value in {
            'UID': f'todo-{new_id}@apichallenges',
            'SUMMARY': create_body['title'],
            'DESCRIPTION': create_body['description'],
            'STATUS': expected_status,
        }.items():
            assert f'{key}:{value}' in lines, f'{key} mismatch: {calendar_response.text!r}'
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(56)
def test_057_get_todos_q_xml_preferred(api_client):
    response = api_client.get(
        TODOS_PATH, headers={'Accept': 'application/json;q=0.5, application/xml;q=1'}
    )
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/xml')
    for todo in todos_from_xml(response.text):
        assert_todo_item(todo)


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(57)
def test_058_get_todos_q_json_preferred(api_client):
    response = api_client.get(
        TODOS_PATH, headers={'Accept': 'application/xml;q=0.5, application/json;q=1'}
    )
    payload = response.json()
    todos = payload['todos']
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    for todo in todos:
        assert_todo_item(todo)


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(58)
def test_059_get_todos_q_reject_all(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.get(TODOS_PATH, headers={'Accept': 'application/json;q=0, application/xml;q=0'})
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=406)
    assert_error_message(
        json.loads(exc.value.body), error_message='No acceptable response type supported'
    )


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(59)
def test_060_get_todos_usupported_and_json(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.get(TODOS_PATH, headers={'Accept': 'application/problem+json'})
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=406)
    assert_error_message(json.loads(exc.value.body), error_message='Unrecognised Accept Type')


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(60)
def test_061_get_todos_text_and_xml(api_client):
    response = api_client.get(TODOS_PATH, headers={'Accept': 'text/xml'})
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='text/xml')
    for todo in todos_from_xml(response.text):
        assert_todo_item(todo)


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(61)
def test_062_get_todos_vendor_xml(api_client):
    response = api_client.get(
        TODOS_PATH, headers={'Accept': 'application/vnd.apichallenges.todo+xml'}
    )
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(
        response=response, expected_content_type='application/vnd.apichallenges.todo+xml'
    )
    for todo in todos_from_xml(response.text):
        assert_todo_item(todo)


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(62)
def test_063_get_todos_xml_wildcard(api_client):
    response = api_client.get(TODOS_PATH, headers={'Accept': 'application/*+xml'})
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/todo+xml')
    for todo in todos_from_xml(response.text):
        assert_todo_item(todo)


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(63)
def test_064_post_todo_xml(api_client):
    body = '''
           <todo>
           <title>test title</title>
           <doneStatus>true</doneStatus>
           <description>created from XML</description>
           </todo>
           '''
    create_response = api_client.post(
        TODOS_PATH,
        content=body,
        headers={'Content-Type': 'application/xml', 'Accept': 'application/xml'},
    )
    new_id = todo_from_xml(create_response.text)['id']
    try:
        assert_status_code(response=create_response, expected_status_code=201)
        assert_content_type(response=create_response, expected_content_type='application/xml')
        assert_todo_item_xml(create_response.text)
        assert_todo_item_matches_xml(
            item=create_response.text,
            expected={'title': 'test title', 'doneStatus': True, 'description': 'created from XML'},
        )
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(65)
def test_065_post_todo_vendor_xml(api_client):
    body = '''
           <todo>
           <title>test title</title>
           <doneStatus>true</doneStatus>
           <description>created with vendor XML</description>
           </todo>
           '''
    create_response = api_client.post(
        TODOS_PATH,
        content=body,
        headers={
            'Content-Type': 'application/vnd.apichallenges.todo+xml',
            'Accept': 'application/json',
        },
    )
    create_payload = create_response.json()
    new_id = create_payload['id']
    try:
        assert_status_code(response=create_response, expected_status_code=201)
        assert_content_type(response=create_response, expected_content_type='application/json')
        assert_todo_item(create_payload)
        assert_todo_item_matches(item=create_payload, expected=request_todo_from_xml(body))
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(66)
def test_066_post_unsupported_content_type(api_client):
    body = {
        'title': 'solution widget todo',
        'doneStatus': True,
        'description': 'created from the solution page',
    }
    with pytest.raises(ApiError) as exc:
        api_client.post(
            TODOS_PATH,
            json=body,
            headers={'Content-Type': 'application/gzip', 'Accept': 'application/json'},
        )
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=415)
    assert_error_message(
        json.loads(exc.value.body), error_message='Unsupported Content Type - application/gzip'
    )


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(67)
def test_067_get_csv_export(api_client):
    get_response = api_client.get(f'{TODOS_PATH}/export?format=csv', headers={'Accept': 'text/csv'})
    assert_status_code(response=get_response, expected_status_code=200)
    assert_content_type(response=get_response, expected_content_type='text/csv')
    todos = todos_from_csv(get_response.text)
    for todo in todos:
        assert_todo_item(todo)


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(68)
def test_068_get_html_export(api_client):
    get_response = api_client.get(
        f'{TODOS_PATH}/export?format=html', headers={'Accept': 'text/html'}
    )
    assert_status_code(response=get_response, expected_status_code=200)
    assert_content_type(response=get_response, expected_content_type='text/html')
    todos = todos_from_html(get_response.text)
    for todo in todos:
        assert_todo_item(todo)


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(69)
def test_069_get_tab_delimited_export(api_client):
    get_response = api_client.get(
        f'{TODOS_PATH}/export?format=tsv', headers={'Accept': 'text/tab-separated-values'}
    )
    assert_status_code(response=get_response, expected_status_code=200)
    assert_content_type(response=get_response, expected_content_type='text/tab-separated-values')
    todos = todos_from_tsv(get_response.text)
    for todo in todos:
        assert_todo_item(todo)


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(78)
def test_078_xml_to_json(api_client):
    body = '''
           <todo>
           <title>test title</title>
           <doneStatus>true</doneStatus>
           <description>created from XML</description>
           </todo>
           '''
    create_response = api_client.post(
        TODOS_PATH,
        content=body,
        headers={'Content-Type': 'application/xml', 'Accept': 'application/json'},
    )
    payload = create_response.json()
    new_id = payload['id']
    try:
        assert_status_code(response=create_response, expected_status_code=201)
        assert_content_type(response=create_response, expected_content_type='application/json')
        assert_todo_item(payload)
        assert_todo_item_matches(
            item=payload,
            expected={'title': 'test title', 'doneStatus': True, 'description': 'created from XML'},
        )
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(79)
def test_079_json_to_xml(api_client):
    body = {'title': 'test title', 'doneStatus': True, 'description': 'created from XML'}
    create_response = api_client.post(
        TODOS_PATH,
        json=body,
        headers={'Content-Type': 'application/json', 'Accept': 'application/xml'},
    )
    new_id = todo_from_xml(create_response.text)['id']
    try:
        assert_status_code(response=create_response, expected_status_code=201)
        assert_content_type(response=create_response, expected_content_type='application/xml')
        assert_todo_item_xml(create_response.text)
        assert_todo_item_matches_xml(
            item=create_response.text,
            expected={'title': 'test title', 'doneStatus': True, 'description': 'created from XML'},
        )
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(98)
def test_098_delete_all_todos(api_client):
    delete_all_rounds = 3
    deleted_todos = []
    get_response = api_client.get(TODOS_PATH)

    assert_status_code(response=get_response, expected_status_code=200)
    assert_content_type(response=get_response, expected_content_type='application/json')
    try:
        for _ in range(delete_all_rounds):
            round_response = api_client.get(TODOS_PATH)
            assert_status_code(response=round_response, expected_status_code=200)
            assert_content_type(response=round_response, expected_content_type='application/json')
            round_todos = round_response.json()['todos']
            if not round_todos:
                break
            for todo in round_todos:
                delete_response = api_client.delete(f'{TODOS_PATH}/{todo['id']}')
                deleted_todos.append(todo)
                assert_status_code(response=delete_response, expected_status_code=204)
        check_delete_response = api_client.get(TODOS_PATH)
        assert_status_code(response=check_delete_response, expected_status_code=200)
        assert_content_type(
            response=check_delete_response, expected_content_type='application/json'
        )
        check_delete_payload = check_delete_response.json()
        check_delete_todos = check_delete_payload['todos']
        assert len(check_delete_todos) == 0, (
            f'Todos list is not empty, neet to delete {len(check_delete_todos)} todo'
        )
    finally:
        for todo in deleted_todos:
            restore_response = api_client.post(
                TODOS_PATH,
                json={
                    'title': todo['title'],
                    'doneStatus': todo['doneStatus'],
                    'description': todo['description'],
                },
            )
            assert_status_code(response=restore_response, expected_status_code=201)


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(99)
def test_099_max_todos(api_client):
    max_todos_count = 20
    new_todo_ids = []
    get_response = api_client.get(TODOS_PATH)

    assert_status_code(response=get_response, expected_status_code=200)
    assert_content_type(response=get_response, expected_content_type='application/json')
    payload = get_response.json()
    todos = payload['todos']
    try:
        for i in range(max_todos_count - len(todos) + 1):
            new_todo = {
                'title': f'Test todo #{len(todos) + i + 1}',
                'doneStatus': True,
                'description': f'Test todo #{len(todos) + i + 1}',
            }
            try:
                create_response = api_client.post(TODOS_PATH, json=new_todo)
            except ApiError as exc:
                assert_error_status_code(
                    received_status_code=exc.status_code, expected_status_code=409
                )
                assert_error_message(
                    json.loads(exc.body),
                    error_message='ERROR: Cannot add instance, maximum limit of 20 reached',
                )
                break
            create_payload = create_response.json()
            assert_status_code(response=create_response, expected_status_code=201)
            assert_content_type(response=create_response, expected_content_type='application/json')
            assert_todo_item_matches(item=create_payload, expected=new_todo)
            new_todo_ids.append(create_payload['id'])
        else:
            pytest.fail('Expected POST /api/todos to return 409 when limit reached')
    finally:
        for todo_id in new_todo_ids:
            delete_response = api_client.delete(f'{TODOS_PATH}/{todo_id}')
            assert_status_code(response=delete_response, expected_status_code=204)


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(36)
def test_100_put_no_id_body(api_client):
    post_body = {'title': 'Test title', 'doneStatus': True, 'description': 'test description'}
    response = api_client.post(TODOS_PATH, json=post_body)
    post_payload = response.json()
    new_id = post_payload['id']
    try:
        assert_status_code(response=response, expected_status_code=201)
        assert_content_type(response=response, expected_content_type='application/json')
        assert_todo_item(post_payload)
        assert_todo_item_matches(item=post_payload, expected=post_body)

        put_body = {
            'title': 'Updated test title',
            'doneStatus': True,
            'description': 'Updated test description',
        }
        put_response = api_client.put(f'{TODOS_PATH}/{new_id}', json=put_body)
        put_payload = put_response.json()
        assert_status_code(response=put_response, expected_status_code=200)
        assert_content_type(response=put_response, expected_content_type='application/json')
        assert_todo_item(put_payload)
        assert_todo_item_matches(item=put_payload, expected=put_body)
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')


@pytest.mark.positive
@pytest.mark.smoke
@pytest.mark.challenge(50)
def test_101_get_todos_application_json(api_client):
    response = api_client.get(TODOS_PATH, headers={'Accept': 'application/json'})
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    payload = response.json()
    todos = payload['todos']
    for todo in todos:
        assert_todo_item(todo)


@pytest.mark.positive
@pytest.mark.smoke
@pytest.mark.challenge(52)
def test_102_get_todos_application_xml_json(api_client):
    response = api_client.get(TODOS_PATH, headers={'Accept': 'application/xml, application/json'})
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/xml')
    payload = response.text
    for todo in todos_from_xml(payload):
        assert_todo_item(todo)


@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(64)
def test_103_create_todo_application_json(api_client):
    post_body = {'title': 'Test title', 'doneStatus': True, 'description': 'test description'}
    response = api_client.post(
        TODOS_PATH,
        headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
        json=post_body,
    )
    post_payload = response.json()
    new_id = post_payload['id']
    try:
        assert_status_code(response=response, expected_status_code=201)
        assert_content_type(response=response, expected_content_type='application/json')
        assert_todo_item(post_payload)
        assert_todo_item_matches(item=post_payload, expected=post_body)
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')
