import pytest

from app.app_setup import AppSetup
from test.unit.common import config_for_tests


@pytest.fixture(scope='function')
def mock_app(tmpdir):
    app_setup = AppSetup(config=config_for_tests(tmpdir))
    return app_setup.app.test_client()


def test_show_profile_page(mock_app):
    response = mock_app.get('/profile', follow_redirects=True)
    assert b'Change User Password' in response.data
