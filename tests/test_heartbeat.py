import json

import pytest

from api_challenges.assertions import (
    assert_error_message,
    assert_error_status_code,
    assert_status_code,
)
from api_challenges.clients import CHALLENGER_HEADER, HEARTBEAT_PATH, ApiError


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(80)
def test_080_delete_heartbeat(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.delete(HEARTBEAT_PATH, headers={'Accept': '*/*'})
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=405)


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(81)
def test_081_patch_heartbeat(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.patch(HEARTBEAT_PATH, headers={'Accept': '*/*'})
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=500)


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(82)
def test_082_trace_heartbeat(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.trace(HEARTBEAT_PATH, headers={'Accept': '*/*'})
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=501)


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
        api_client.get(
            HEARTBEAT_PATH,
            headers={
                'Accept': 'application/json',
                CHALLENGER_HEADER: api_client.challenger + 'x' * 100,
            },
        )
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=431)
    assert_error_message(
        item=json.loads(exc.value.body),
        error_message='X-CHALLENGER header is too large, maximum allowed is 100 characters',
    )


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(85)
def test_085_post_as_delete_heartbeat(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.post(
            HEARTBEAT_PATH, headers={'X-HTTP-Method-Override': 'DELETE', 'Accept': '*/*'}
        )
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=405)


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(86)
def test_086_post_as_patch_heartbeat(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.post(
            HEARTBEAT_PATH, headers={'X-HTTP-Method-Override': 'PATCH', 'Accept': '*/*'}
        )
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=500)


@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.challenge(87)
def test_087_post_as_trace_heartbeat(api_client):
    with pytest.raises(ApiError) as exc:
        api_client.post(
            HEARTBEAT_PATH, headers={'X-HTTP-Method-Override': 'TRACE', 'Accept': '*/*'}
        )
    assert_error_status_code(received_status_code=exc.value.status_code, expected_status_code=501)
