import json

import pytest

from api_challenges.assertions import (
    assert_content_type,
    assert_error_message,
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
    assert_error_message(json.loads(exc.value.body),
                         error_message='404 resource Unknown')

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
    assert_error_message(json.loads(exc.value.body),
                         error_message='Could not find an instance with todos/999999')

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
    assert_error_message(json.loads(exc.value.body),
                         error_message=f'Could not find an instance with todos/{new_id}')

@pytest.mark.negative
@pytest.mark.regression
def test_012_create_empty_body_todo(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.post(TODOS_PATH, json={})
    assert exc.value.status_code == 422
    assert_error_message(json.loads(exc.value.body),
                         error_message='title : field is mandatory')

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(25)
def test_013_create_todo_too_long_title(api_client):
    body = {'title': 'T'*51, 'doneStatus': True, 'description': 'test description'}
    with pytest.raises(ApiError) as exc:
        api_client.post(TODOS_PATH, json=body)
    assert exc.value.status_code == 422
    assert_error_message(json.loads(exc.value.body),
                         error_message='Failed Validation: Maximum allowable length exceeded for '
                                       'title - maximum allowed is 50')

@pytest.mark.negative
@pytest.mark.regression
def test_014_create_todo_id_in_body(api_client):
    body = {'id': 1, 'title': 'Test title', 'doneStatus': True, 'description': 'test description'}
    with pytest.raises(ApiError) as exc:
        api_client.post(TODOS_PATH, json=body)
    assert exc.value.status_code == 422
    assert_error_message(json.loads(exc.value.body),
                         error_message='Failed Validation: Invalid Creation: Not allowed to create '
                                       'with id')

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
                       '153*157*161*165*169*173*177*181*185*189*193*197*201*'}
    with pytest.raises(ApiError) as exc:
        api_client.post(TODOS_PATH, json=body)
    assert exc.value.status_code == 422
    assert_error_message(json.loads(exc.value.body),
                         error_message='Failed Validation: Maximum allowable length exceeded for '
                         'description - maximum allowed is 200')

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(27)
def test_035_max_out_content(api_client):
    body = {
        'title': '2*4*6*8*11*14*17*20*23*26*29*32*35*38*41*44*47*50*',
        'doneStatus': True,
        'description': '*3*5*7*9*12*15*18*21*24*27*30*33*36*39*42*45*48*51*54*57*60*63*66*69*72*75*'
                       '78*81*84*87*90*93*96*100*104*108*112*116*120*124*128*132*136*140*144*148*'
                       '152*156*160*164*168*172*176*180*184*188*192*196*200*'}
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
    body = {
        'title': 'too much content',
        'doneStatus': True,
        'description': 'D'*5001}
    with pytest.raises(ApiError) as exc:
        api_client.post(TODOS_PATH, json=body)
    assert exc.value.status_code == 413
    assert_error_message(json.loads(exc.value.body),
                         error_message='Error: request body too large, max allowed is 5000 bytes')

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(29)
def test_037_extra_field(api_client):
    body = {
        'title': 'extra field',
        'doneStatus': True,
        'description': 'Test description',
        'priority': 'high'
    }
    with pytest.raises(ApiError) as exc:
        api_client.post(TODOS_PATH, json=body)
    assert exc.value.status_code == 422
    assert_error_message(json.loads(exc.value.body),
                         error_message='Failed Validation: Could not find field: priority')

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
    assert exc.value.status_code == 422
    assert_error_message(json.loads(exc.value.body),
                         error_message='Cannot create todo with PUT due to Auto fields id')

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(31)
def test_039_update_via_post(api_client):
    create_body = {
        'title': 'test title',
        'doneStatus': False,
        'description': 'test description'}
    updated_body = {
        'title': 'solution widget todo',
        'doneStatus': True,
        'description': 'created from the solution page'}
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
        'description': 'created from the solution page'}
    with pytest.raises(ApiError) as exc:
        api_client.post(f'{TODOS_PATH}/9999', json=body)
    assert exc.value.status_code == 404
    assert_error_message(json.loads(exc.value.body),
                     error_message='No such todo entity instance with id == 9999 found')

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(33)
def test_041_update_via_put_full(api_client):
    create_body = {
        'title': 'test title',
        'doneStatus': False,
        'description': 'test description'}
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
            'description': 'created from the solution page'}

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
    create_body = {
        'title': 'test title',
        'doneStatus': False,
        'description': 'test description'}
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
            'description': 'created from the solution page'}

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
    body = {
        'doneStatus': True,
        'description': 'created from the solution page'}
    with pytest.raises(ApiError) as exc:
        api_client.put(f'{TODOS_PATH}/10', json=body)
    assert exc.value.status_code == 422
    assert_error_message(json.loads(exc.value.body),
                     error_message='Failed Validation: title : field is mandatory')

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(38)
def test_044_update_via_put_no_id(api_client):
    body = {
        'title': 'update widget todo without id',
        'doneStatus': True,
        'description': 'created from the solution page'}
    with pytest.raises(ApiError) as exc:
        api_client.put(TODOS_PATH, json=body)
    assert exc.value.status_code == 422
    assert_error_message(json.loads(exc.value.body),
                     error_message='PUT requires an identifier in the URI or payload')

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(40)
def test_045_update_via_put_amend_id(api_client):
    body = {
        'id': 9999,
        'title': 'update widget todo without id',
        'doneStatus': True,
        'description': 'created from the solution page'}
    with pytest.raises(ApiError) as exc:
        api_client.put(f'{TODOS_PATH}/3', json=body)
    assert exc.value.status_code == 422
    assert_error_message(json.loads(exc.value.body),
                     error_message='Can not amend id from 3 to 9999')

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
        patch_response = api_client.patch(f'{TODOS_PATH}/{new_id}',
                                          headers={'Content-Type': 'application/merge-patch+json'},
                                          json=patch_body)
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

        patch_body = [
          {
            "op": "replace",
            "path": "/title",
            "value": "patched with json patch"
          }
        ]
        patch_response = api_client.patch(f'{TODOS_PATH}/{new_id}',
                                          headers={'Content-Type': 'application/json-patch+json'},
                                          json=patch_body)
        patch_payload = patch_response.json()
        patch_expected = {**post_payload, 'title': 'patched with json patch'}
        assert_status_code(response=patch_response, expected_status_code=200)
        assert_content_type(response=patch_response, expected_content_type='application/json')
        assert_todo_item(patch_payload)
        assert_todo_item_matches(item=patch_payload, expected=patch_expected)
    finally:
        api_client.delete(f'{TODOS_PATH}/{new_id}')
