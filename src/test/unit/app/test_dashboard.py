import pytest

from app.app import APP


@pytest.fixture(scope='function')
def mock_app():
    return APP.test_client()


def test_home_dashboard(mock_app):
    response = mock_app.get('/')
    assert response
