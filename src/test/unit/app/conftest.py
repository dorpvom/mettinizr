import pytest
from mongomock import MongoClient  # pylint: disable=import-error

from app.app_setup import AppSetup
from test.unit.common import config_for_tests, MockUser, simple_session  # pylint: disable=wrong-import-order


@pytest.fixture(scope='function')
def app_fixture(tmpdir, monkeypatch):
    monkeypatch.setattr('database.mett_store.MongoClient', MongoClient)
    return AppSetup(config=config_for_tests(tmpdir))


@pytest.fixture(scope='function')
def mock_app(app_fixture):  # pylint: disable=redefined-outer-name
    app_fixture.user_database.create_all()

    with simple_session(app_fixture.user_database):
        app_fixture.user_interface.create_user(email=MockUser.email, password=MockUser.password)
        app_fixture.user_interface.create_role(name=app_fixture.config.get('User', 'default_role'))

    return app_fixture.app.test_client()
