import pytest

from app.app_setup import AppSetup
from test.unit.common import config_for_tests


class MockUser:
    email = 'mock_user_name'
    is_authenticated = True


@pytest.fixture(scope='function')
def mock_app(tmpdir):
    app_setup = AppSetup(config=config_for_tests(tmpdir))
    app_setup.user_database.create_all()
    app_setup.user_interface.create_user(email='mock_user_name', password='old_password')
    return app_setup.app.test_client()


def test_show_profile_page(mock_app):
    response = mock_app.get('/profile')
    assert b'Change User Password' in response.data


def test_profile_new_password(mock_app, monkeypatch):
    monkeypatch.setattr('app.profile.current_user', MockUser())
    response = mock_app.post('/profile', data={'new_password': 'any_password', 'new_password_confirm': 'any_password', 'old_password': 'old_password'}, follow_redirects=True)
    assert response.status_code == 200
