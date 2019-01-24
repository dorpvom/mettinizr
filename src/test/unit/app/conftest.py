import pytest
from mongomock import MongoClient

from app.app_setup import AppSetup
from test.unit.common import config_for_tests


@pytest.fixture(scope='function')
def app_setup(tmpdir, monkeypatch):
    monkeypatch.setattr('database.mett_store.MongoClient', MongoClient)
    return AppSetup(config=config_for_tests(tmpdir))


@pytest.fixture(scope='function')
def mock_app(app_setup):
    app_setup.user_database.create_all()
    app_setup.user_interface.create_user(email='mock_user_name', password='old_password')
    return app_setup.app.test_client()
