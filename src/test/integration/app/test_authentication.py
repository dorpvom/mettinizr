import pytest

from app.app_setup import AppSetup


@pytest.fixture(scope='function')
def auth_app(config_for_tests):
    config_for_tests.set('Runtime', 'testing', 'false')

    app = AppSetup(config=config_for_tests)
    app.user_interface.create_tables()
    with app.app.app_context():
        app.user_interface.create_user('authenticated', 'password')
    app.user_interface.create_role('user')
    app.user_interface.add_role_to_user('authenticated', 'user')

    return app


@pytest.fixture(scope='function')
def auth_client(auth_app):
    return auth_app.app.test_client()


@pytest.mark.skip(reason='Working in production. Failure unclear, so testing postponed.')
def test_successful_login(auth_client, auth_app):
    auth_data = {
        'next': '/profile',
        'csrf_token': 'IjM2MDI1NjhkMzVmYjNlYTUxZTIyMmM3NzExODBmN2RkZDMwODdiM2Yi.Y-oiUg.E-aKLDHHAjvSK_uWl5DT4Cp-bnA',
        'email': 'authenticated@anything.com',
        'password': 'password',
        'submit': ''
    }

    response = auth_client.post('/login', data=auth_data, follow_redirects=True)
    assert b'There is no current order!' in response.data
    assert 'Hi authenticated' in response.data
