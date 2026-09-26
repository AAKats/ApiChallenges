import pytest

from api_challenges.assertions import (
    assert_challenge_item,
    assert_content_type,
    assert_status_code,
    assert_valid_guid,
)

pytestmark = pytest.mark.smoke


@pytest.mark.positive
@pytest.mark.challenge(1)
def test_001_challenger_guid_is_valid(api_client):
    guid = api_client.challenger
    assert guid is not None, 'X-CHALLENGER missing: POST /api/challenger was not run in fixture'
    assert_valid_guid(guid)


@pytest.mark.positive
@pytest.mark.challenge(2)
def test_002_get_all_challenges(api_client):
    response = api_client.get('/api/challenges')
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    assert response.headers.get('X-CHALLENGER') == api_client.challenger, (
        'server did not echo back session header'
    )
    payload = response.json()
    challenges = payload['challenges']
    for challenge in challenges:
        assert_challenge_item(challenge)
