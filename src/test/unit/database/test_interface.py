import pytest

from app.app_setup import AppSetup
from database.database import DatabaseError
from database.interface import MettInterface


@pytest.fixture(scope='function')
def app(config_for_tests):
    return AppSetup(config=config_for_tests)


@pytest.fixture(scope='function')
def interface(app, config_for_tests):
    interface = MettInterface(config_for_tests)
    interface.create_tables()

    with app.app.app_context():
        interface.create_user('user', 'user')
        interface.create_role('role')

    return interface


def test_role_creation(interface):
    assert not interface.role_exists('foo')
    interface.create_role('foo')
    assert interface.role_exists('foo')


def test_get_user(interface):
    assert interface.get_user('user')


def test_role_addition(interface):
    assert not interface.get_user('user').roles
    interface.add_role_to_user('user', 'role')
    assert interface.get_user('user').roles[0].name == 'role'


def test_add_bun_class(interface):
    assert not interface.bun_class_exists('donut')
    interface.add_bun_class('donut', 1.0, 50.0)
    assert interface.bun_class_exists('donut')
    assert 'donut' in interface.list_bun_classes()


def test_create_order(interface):
    assert not interface.active_order_exists()
    interface.create_order(expiry_date='2100-01-01')  # If this ever fails, I did something right ; )
    assert interface.active_order_exists()
    assert not interface.current_order_is_expired()


def test_create_order_expired(interface):
    assert not interface.active_order_exists()
    with pytest.raises(DatabaseError):
        interface.create_order(expiry_date='2000-01-01')
