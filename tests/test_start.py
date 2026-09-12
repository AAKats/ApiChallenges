import re

import pytest

from api_challenges.assertions import assert_challenge_item, assert_content_type, assert_status_code

pytestmark = pytest.mark.smoke

GUID_RE = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}')

@pytest.mark.positive
def test_001_challenger_guid_is_valid(api_client):
    guid = api_client.challenger
    assert guid is not None, 'X-CHALLENGER missing: POST /api/challenger was not run in fixture'
    assert GUID_RE.fullmatch(guid), f'Incorrect GUID format: {guid!r}'

@pytest.mark.positive
def test_002_get_all_challenges(api_client):
    response = api_client.get('/api/challenges')
    assert_status_code(response=response, expected_status_code=200)
    assert_content_type(response=response, expected_content_type='application/json')
    assert response.headers.get('X-CHALLENGER') == api_client.challenger, \
        'server did not echo back session header'
    payload = response.json()
    challenges = payload['challenges']
    for challenge in challenges:
        assert_challenge_item(challenge)

