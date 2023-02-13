import pytest

from app.app_setup import AppSetup
from test.unit.common import TestUser  # pylint: disable=wrong-import-order


@pytest.fixture(scope='function', autouse=True)
def patch_current_user(monkeypatch):
    monkeypatch.setattr('app.dashboard.current_user', TestUser())


@pytest.fixture(scope='function')
def app_fixture(config_for_tests, monkeypatch):
    config_for_tests.set('Runtime', 'behind_proxy', 'true')
    return AppSetup(config=config_for_tests)


@pytest.fixture(scope='function')
def client_fixture(app_fixture):  # pylint: disable=redefined-outer-name
    app_fixture.database.create_tables()
    app_fixture.database.initialize_bun_classes()

    with app_fixture.app.app_context():
        app_fixture.database.create_user(name=TestUser.name, password=TestUser.password)

    return app_fixture.app.test_client()


def test_home_under_suffix(client_fixture):
    assert client_fixture.get('/mett/').status_code == 200
