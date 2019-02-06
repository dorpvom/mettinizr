import pytest
from mongomock import MongoClient

from app.app_setup import AppSetup
from create_initial_user import create_init_user
from test.unit.common import config_for_tests


@pytest.fixture(scope='function')
def app_fixture(monkeypatch, tmpdir):
    monkeypatch.setattr('database.mett_store.MongoClient', MongoClient)
    return AppSetup(config_for_tests(tmpdir))


def test_create_init_user(app_fixture):
    create_init_user(app_fixture)

    assert app_fixture.mett_store.account_exists('init')
    assert app_fixture.user_interface.find_role('admin')
    assert app_fixture.user_interface.find_role('user')

    user = app_fixture.user_interface.find_user(email='init')
    assert user
    assert len(user.roles) == 1
