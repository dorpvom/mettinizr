from configparser import ConfigParser
from pathlib import Path

import pytest

from app.app_setup import AppSetup
from database.database import DatabaseError
from database.database_objects import UserEntry, RoleEntry
from database.interface import MettInterface

DEFAULT_CONFIG_FILE = Path(Path(__file__).parent.parent.parent.parent, 'config', 'app.config')


@pytest.fixture(scope='function')
def create_test_config():
    config = ConfigParser()
    config.read(str(DEFAULT_CONFIG_FILE))

    config.set('Database', 'database_path', ':memory:')

    return config

@pytest.fixture(scope='function')
def database(create_test_config):
    interface = MettInterface(create_test_config)
    interface.create_tables()
    return interface


@pytest.fixture(scope='function')
def app(create_test_config):
    return AppSetup(create_test_config)


def test_create_user(database, app):
    assert not database.user_exists('test')

    with app.app.app_context():
        user = database.create_user('test', 'test', is_hashed=False)

    assert isinstance(user, UserEntry)
    assert database.user_exists('test')


def test_create_role(database):
    assert not database.role_exists('test')

    role = database.create_role('test')

    assert isinstance(role, RoleEntry)
    assert database.role_exists('test')


def test_add_role_to_user(database, app):
    with app.app.app_context():
        database.create_user('test', 'test', is_hashed=False)
    database.create_role('test')

    with database.get_read_write_session() as session:
        assert not session.get(UserEntry, 'test').roles

    database.add_role_to_user('test', 'test')

    with database.get_read_write_session() as session:
        assert session.get(UserEntry, 'test').roles


def test_add_bun_class(database):
    assert not database.bun_class_exists('test')

    database.add_bun_class('test', '1.00', '100')

    assert database.bun_class_exists('test')


def test_create_expired_order_fails(database):
    with pytest.raises(DatabaseError):
        database.create_order(expiry_date='2022-02-10')


def test_create_order(database):
    assert not database.active_order_exists()

    database.create_order(expiry_date='2023-02-10')

    assert database.active_order_exists()
    assert not database.current_order_is_expired()
