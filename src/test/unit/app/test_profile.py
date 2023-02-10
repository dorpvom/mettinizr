import pytest

from test.unit.common import TestUser


@pytest.fixture(scope='function', autouse=True)
def patch_current_user(monkeypatch):
    monkeypatch.setattr('app.profile.current_user', TestUser())


def test_show_profile_page(client):
    response = client.get('/profile')
    assert b'Change password' in response.data


def test_profile_new_password(client):
    response = client.post('/profile', data={'new_password': 'any_password', 'new_password_confirm': 'any_password', 'old_password': TestUser.password})
    assert b'password change successful' in response.data


def test_profile_wrong_password(client):
    response = client.post('/profile', data={'new_password': 'any_password', 'new_password_confirm': 'any_password', 'old_password': 'false_password'})
    assert b'wrong password' in response.data


def test_profile_non_matching_password(client):
    response = client.post('/profile', data={'new_password': 'any_password', 'new_password_confirm': 'other_password', 'old_password': 'old_password'})
    assert b'new password did not match' in response.data


def test_profile_illegal_password(client):
    response = client.post('/profile', data={'new_password': '', 'new_password_confirm': '', 'old_password': TestUser.password})
    assert b'password is not legal' in response.data
