import io

import pytest

from app.app_setup import AppSetup
from test.unit.common import config_for_tests
from manage_users import prompt_for_actions


@pytest.fixture(scope='function')
def mock_config(tmpdir):
    return config_for_tests(tmpdir)


@pytest.fixture(scope='function')
def app_fixture(mock_config):
    setup = AppSetup(mock_config)
    setup.user_database.create_all()
    return setup


def test_create_user(app_fixture, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('create_user\ntest\ntest\n\0'))

    assert not app_fixture.user_interface.user_exists('test')
    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    assert app_fixture.user_interface.user_exists('test')


def test_create_role(app_fixture, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('create_role\ntest\n\0'))

    assert not app_fixture.user_interface.role_exists('test')
    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    assert app_fixture.user_interface.role_exists('test')
