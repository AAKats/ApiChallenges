import json

import pytest

from api_challenges.assertions import assert_error_message, assert_status_code
from api_challenges.clients import CHALLENGER_HEADER, HEARTBEAT_PATH, ApiError


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(80)
def test_080_delete_heartbeat(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.delete(HEARTBEAT_PATH,
                          headers={
                              'Accept': '*/*'
                          })
    assert exc.value.status_code == 405, \
        f'Incorrect status code: {exc.value.status_code}, should be: 405'

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(81)
def test_081_patch_heartbeat(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.patch(HEARTBEAT_PATH,
                          headers={
                              'Accept': '*/*'
                          })
    assert exc.value.status_code == 500, \
        f'Incorrect status code: {exc.value.status_code}, should be: 500'

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(82)
def test_082_trace_heartbeat(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.trace(HEARTBEAT_PATH,
                          headers={
                              'Accept': '*/*'
                          })
    assert exc.value.status_code == 501, \
        f'Incorrect status code: {exc.value.status_code}, should be: 501'

@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.challenge(83)
def test_083_get_heartbeat(api_client):
    response = api_client.get(HEARTBEAT_PATH, headers={'Accept': '*/*'})
    assert_status_code(response=response, expected_status_code=204)

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(84)
def test_084_too_long_xchallenger_heartbeat(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.get(HEARTBEAT_PATH,
                                  headers={
                                           'Accept': 'application/json',
                                           CHALLENGER_HEADER: api_client.challenger + 'x'*100
                                  })
    assert exc.value.status_code == 431, \
        f'Incorrect status code: {exc.value.status_code}, should be: 431'
    assert_error_message(item=json.loads(exc.value.body),
                         error_message='X-CHALLENGER header is too large,'
                                       ' maximum allowed is 100 characters')

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(85)
def test_085_post_as_delete_heartbeat(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.post(HEARTBEAT_PATH,
                          headers={
                              'X-HTTP-Method-Override': 'DELETE',
                              'Accept': '*/*'
                          })
    assert exc.value.status_code == 405, \
        f'Incorrect status code: {exc.value.status_code}, should be: 405'

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(86)
def test_081_post_as_patch_heartbeat(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.post(HEARTBEAT_PATH,
                          headers={
                              'X-HTTP-Method-Override': 'PATCH',
                              'Accept': '*/*'
                          })
    assert exc.value.status_code == 500, \
        f'Incorrect status code: {exc.value.status_code}, should be: 500'

@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(86)
def test_086_post_as_trace_heartbeat(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.post(HEARTBEAT_PATH,
                          headers={
                              'X-HTTP-Method-Override': 'TRACE',
                              'Accept': '*/*'
                          })
    assert exc.value.status_code == 501, \
        f'Incorrect status code: {exc.value.status_code}, should be: 501'
