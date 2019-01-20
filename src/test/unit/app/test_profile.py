import pytest

from test.unit.common import MockUser


@pytest.fixture(scope='function', autouse=True)
def patch_current_user(monkeypatch):
    monkeypatch.setattr('app.profile.current_user', MockUser())


def test_show_profile_page(mock_app):
    response = mock_app.get('/profile')
    assert b'Change User Password' in response.data


def test_profile_new_password(mock_app):
    response = mock_app.post('/profile', data={'new_password': 'any_password', 'new_password_confirm': 'any_password', 'old_password': 'old_password'}, follow_redirects=True)
    assert response.status_code == 200
