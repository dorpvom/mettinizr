import pytest
from mongomock import MongoClient  # pylint: disable=import-error

from app.app_setup import AppSetup
from test.unit.common import config_for_tests, MockUser  # pylint: disable=wrong-import-order


@pytest.fixture(scope='function', autouse=True)
def patch_current_user(monkeypatch):
    monkeypatch.setattr('app.dashboard.current_user', MockUser())


@pytest.fixture(scope='function')
def app_fixture(tmpdir, monkeypatch):
    monkeypatch.setattr('database.mett_store.MongoClient', MongoClient)
    monkeypatch.setattr('database.user_store.MongoClient', MongoClient)
    config = config_for_tests(tmpdir)
    config.set('Runtime', 'behind_proxy', 'true')
    return AppSetup(config=config)


@pytest.fixture(scope='function')
def mock_app(app_fixture):  # pylint: disable=redefined-outer-name
    with app_fixture.app.app_context():
        app_fixture.user_interface.create_user(name=MockUser.name, password=MockUser.password)

    app_fixture.mett_store.create_account(MockUser.name)

    return app_fixture.app.test_client()


def test_home_under_suffix(mock_app):
    assert mock_app.get('/mett/').status_code == 200
