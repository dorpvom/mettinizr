import io

import pytest
from mongomock import MongoClient

from app.app_setup import AppSetup
from manage_users import prompt_for_actions
from test.unit.common import config_for_tests


@pytest.fixture(scope='function')
def mock_config(tmpdir):
    return config_for_tests(tmpdir)


@pytest.fixture(scope='function')
def app_fixture(mock_config, monkeypatch):
    monkeypatch.setattr('database.mett_store.MongoClient', MongoClient)
    setup = AppSetup(mock_config)
    setup.user_database.create_all()
    return setup


def test_create_user(app_fixture, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('create_user\ntest\n\0'))
    monkeypatch.setattr('manage_users.getpass._raw_input', lambda *_, input: 'test')  # stdin mocking does not seem to work here ..

    assert not app_fixture.user_interface.user_exists('test')
    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    assert app_fixture.user_interface.user_exists('test')


def test_create_role(app_fixture, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('create_role\ntest\n\0'))

    assert not app_fixture.user_interface.role_exists('test')
    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    assert app_fixture.user_interface.role_exists('test')


def test_show_help(app_fixture, monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO('help\n\0'))

    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    out, _ = capsys.readouterr()
    assert 'show this help' in out
