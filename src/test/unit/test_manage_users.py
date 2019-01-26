import io

import pytest
from mongomock import MongoClient

from app.app_setup import AppSetup
from manage_users import prompt_for_actions, start_user_management
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
    monkeypatch.setattr('manage_users.getpass.getpass', lambda *_: 'test')  # stdin mocking does not seem to work here ..

    assert not app_fixture.user_interface.user_exists('test')
    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    assert app_fixture.user_interface.user_exists('test')


def test_create_user_exists(app_fixture, monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO('create_user\ntest\n\0'))
    monkeypatch.setattr('manage_users.getpass.getpass', lambda *_: 'test')  # stdin mocking does not seem to work here ..

    app_fixture.user_interface.create_user(email='test', password='test')
    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    out, _ = capsys.readouterr()
    assert 'user must not exist' in out


def test_create_user_empty_password(app_fixture, monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO('create_user\ntest\n\0'))
    monkeypatch.setattr('manage_users.getpass.getpass', lambda *_: '')  # stdin mocking does not seem to work here ..

    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    out, _ = capsys.readouterr()
    assert 'password is illegal' in out


def test_create_user_name_too_long(app_fixture, monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO('create_user\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n\0'))
    monkeypatch.setattr('manage_users.getpass.getpass', lambda *_: '')  # stdin mocking does not seem to work here ..

    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    out, _ = capsys.readouterr()
    assert 'input too long' in out


def test_create_role(app_fixture, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('create_role\ntest\n\0'))

    assert not app_fixture.user_interface.role_exists('test')
    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    assert app_fixture.user_interface.role_exists('test')


def test_create_role_exists(app_fixture, monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO('create_role\ntest\n\0'))
    app_fixture.user_interface.create_role(name='test')

    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    out, _ = capsys.readouterr()
    assert 'role must not exist' in out


def test_add_role_to_user(app_fixture, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('add_role_to_user\ntest\ntest\n\0'))
    app_fixture.user_interface.create_user(email='test', password='test')
    app_fixture.user_interface.create_role(name='test')
    app_fixture.user_database.session.commit()

    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)

    user = app_fixture.user_interface.find_user(email='test')
    assert user.roles[0].name == 'test'


def test_add_role_no_user(app_fixture, monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO('add_role_to_user\ntest\ntest\n\0'))

    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    out, _ = capsys.readouterr()
    assert 'user must exists before adding it to role' in out


def test_add_role_no_role(app_fixture, monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO('add_role_to_user\ntest\ntest\n\0'))
    app_fixture.user_interface.create_user(email='test', password='test')
    app_fixture.user_database.session.commit()

    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    out, _ = capsys.readouterr()
    assert 'role must exists before user can be added' in out


def test_remove_role_from_user(app_fixture, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('remove_role_from_user\ntest\ntest\n\0'))
    app_fixture.user_interface.create_user(email='test', password='test')
    app_fixture.user_interface.create_role(name='test')
    app_fixture.user_interface.add_role_to_user(user=app_fixture.user_interface.find_user(email='test'), role='test')
    app_fixture.user_database.session.commit()

    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)

    user = app_fixture.user_interface.find_user(email='test')
    assert len(user.roles) == 0


def test_remove_role_no_user(app_fixture, monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO('remove_role_from_user\ntest\ntest\n\0'))

    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    out, _ = capsys.readouterr()
    assert 'user must exists before removing role from it' in out


def test_remove_role_no_role(app_fixture, monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO('remove_role_from_user\ntest\ntest\n\0'))
    app_fixture.user_interface.create_user(email='test', password='test')
    app_fixture.user_database.session.commit()

    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    out, _ = capsys.readouterr()
    assert 'role must exists before removing it from user' in out


def test_delete_user(app_fixture, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('delete_user\ntest\n\0'))
    app_fixture.user_interface.create_user(email='test', password='test')
    app_fixture.user_database.session.commit()

    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    assert not app_fixture.user_interface.find_user(email='test')


def test_delete_user_no_user(app_fixture, monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO('delete_user\ntest\n\0'))

    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    out, _ = capsys.readouterr()
    assert 'user must exists before deleting it' in out


def test_show_help_and_exit(app_fixture, monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO('help\nexit\n'))

    prompt_for_actions(app_fixture.app, app_fixture.user_interface, app_fixture.user_database, app_fixture.mett_store)
    out, _ = capsys.readouterr()
    assert 'show this help' in out
    assert 'Quitting ..' in out


def test_start_user_management(app_fixture, monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO('exit\n'))

    start_user_management(app_fixture)
    out, _ = capsys.readouterr()
    assert 'Quitting ..' in out
