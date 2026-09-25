import pytest

from api_challenges.assertions import (
    assert_content_type,
    assert_error_status_code,
    assert_note_item,
    assert_note_item_matches,
    assert_status_code,
    assert_valid_guid,
)
from api_challenges.clients import SECRET_PATH, ApiError


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(88)
def test_088_incorrect_user_password(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.get(f'{SECRET_PATH}/token',
                       headers={
                           'Authorization': 'Test YWRtaW46cGFzc3dvcmRk',
                           'Accept': '*/*'
                       })
        assert_error_status_code(
            received_status_code=exc.value.status_code,
            expected_status_code=401,
        )

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(89)
def test_089_correct_user_password(api_client):
    response = api_client.get(f'{SECRET_PATH}/token',
                              headers={
                                  'Authorization': 'Basic YWRtaW46cGFzc3dvcmQ=',
                                  'Accept': '*/*'
                              })
    token = response.json()['token']
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    assert_valid_guid(token)

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(90)
def test_090_not_valid_auth_token(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.get(f'{SECRET_PATH}/note',
                       headers={
                           'X-AUTH-TOKEN': 'incorrect_token',
                           'Accept': 'application/json'
                       })
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=403)

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(91)
def test_091_no_auth_token(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.get(f'{SECRET_PATH}/note',
                       headers={
                           'Accept': 'application/json'
                       })
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=401)

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(92)
def test_092_valid_auth_token(api_client):
    get_token_response = api_client.get(f'{SECRET_PATH}/token',
                              headers={
                                  'Authorization': 'Basic YWRtaW46cGFzc3dvcmQ=',
                                  'Accept': '*/*'
                              })
    x_auth_token = get_token_response.json()['token']
    assert_status_code(response=get_token_response, expected_status_code=200)
    assert_content_type(response=get_token_response, expected_content_type='application/json')
    assert_valid_guid(x_auth_token)

    response = api_client.get(f'{SECRET_PATH}/note',
                              headers={
                                  'X-AUTH-TOKEN': x_auth_token,
                                  'Accept': 'application/json'
                              })
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(93)
def test_093_create_note(api_client):
    get_token_response = api_client.get(f'{SECRET_PATH}/token',
                              headers={
                                  'Authorization': 'Basic YWRtaW46cGFzc3dvcmQ=',
                                  'Accept': '*/*'
                              })
    x_auth_token = get_token_response.json()['token']
    assert_status_code(response=get_token_response, expected_status_code=200)
    assert_content_type(response=get_token_response, expected_content_type='application/json')
    assert_valid_guid(x_auth_token)

    body = {'note': 'Test note'}
    response = api_client.post(f'{SECRET_PATH}/note',
                              headers={
                                  'X-AUTH-TOKEN': x_auth_token,
                                  'Accept': 'application/json',
                                  'Content-Type': 'application/json'
                              }, json=body)
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    note_payload = response.json()
    assert_note_item(note_payload)
    assert_note_item_matches(item=note_payload, expected=body)

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(94)
def test_094_create_note_no_auth_token(api_client):
    body = {'note': 'Test note'}
    with pytest.raises(ApiError) as exc:
        api_client.post(f'{SECRET_PATH}/note',
                        headers={
                            'Accept': 'application/json',
                            'Content-Type': 'application/json'
                        }, json=body)
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=401)

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(95)
def test_095_create_note_wrong_auth_token(api_client):
    body = {'note': 'Test note'}
    with pytest.raises(ApiError) as exc:
        api_client.post(f'{SECRET_PATH}/note',
                        headers={
                            'X-AUTH-TOKEN': 'wrong_token',
                            'Accept': 'application/json',
                            'Content-Type': 'application/json'
                        }, json=body)
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=403)

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(96)
def test_096_valid_bearer_token(api_client):
    get_token_response = api_client.get(f'{SECRET_PATH}/token',
                              headers={
                                  'Authorization': 'Basic YWRtaW46cGFzc3dvcmQ=',
                                  'Accept': '*/*'
                              })
    x_auth_token = get_token_response.json()['token']
    assert_status_code(response=get_token_response, expected_status_code=200)
    assert_content_type(response=get_token_response, expected_content_type='application/json')
    assert_valid_guid(x_auth_token)

    response = api_client.get(f'{SECRET_PATH}/note',
                              headers={
                                  'Authorization': f'Bearer {x_auth_token}',
                                  'Accept': 'application/json'
                              })
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(97)
def test_097_create_note_bearer(api_client):
    get_token_response = api_client.get(f'{SECRET_PATH}/token',
                              headers={
                                  'Authorization': 'Basic YWRtaW46cGFzc3dvcmQ=',
                                  'Accept': '*/*'
                              })
    x_auth_token = get_token_response.json()['token']
    assert_status_code(response=get_token_response, expected_status_code=200)
    assert_content_type(response=get_token_response, expected_content_type='application/json')
    assert_valid_guid(x_auth_token)

    body = {'note': 'Test note bearer'}
    response = api_client.post(f'{SECRET_PATH}/note',
                              headers={
                                  'Authorization': f'Bearer {x_auth_token}',
                                  'Accept': 'application/json',
                                  'Content-Type': 'application/json'
                              }, json=body)
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    note_payload = response.json()
    assert_note_item(note_payload)
    assert_note_item_matches(item=note_payload, expected=body)