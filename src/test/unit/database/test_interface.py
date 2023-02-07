import pytest

from app.app_setup import AppSetup
from database.database import DatabaseError
from database.interface import MettInterface
from test.unit.common import HAS_NOT_EXPIRED, HAS_EXPIRED


@pytest.fixture(scope='function')
def app(config_for_tests):
    return AppSetup(config=config_for_tests)


@pytest.fixture(scope='function')
def interface(app, config_for_tests):
    interface = MettInterface(config_for_tests)
    interface.create_tables()
    interface.initialize_bun_classes()

    with app.app.app_context():
        interface.create_user('user', 'user')

    interface.create_role('role')

    return interface


def test_create_role(interface):
    assert not interface.role_exists('foo')
    assert not interface.get_role('foo')

    interface.create_role('foo')

    assert interface.role_exists('foo')
    assert interface.get_role('foo')


def test_create_user(interface, app):
    assert not interface.get_user('foo')
    with app.app.app_context():
        interface.create_user('foo', 'foo')
    assert interface.get_user('foo')


def test_create_user_exists(interface, app):
    with pytest.raises(DatabaseError):
        interface.create_user('user', 'user')


def test_get_user(interface):
    assert interface.get_user('user')


def test_role_addition(interface):
    assert not interface.get_user('user').roles
    interface.add_role_to_user('user', 'role')
    assert interface.get_user('user').roles[0].name == 'role'


def test_role_addition_errors(interface):
    with pytest.raises(DatabaseError):
        interface.add_role_to_user('user', 'non-existent')
    with pytest.raises(DatabaseError):
        interface.add_role_to_user('non-existent', 'role')

    interface.add_role_to_user('user', 'role')
    with pytest.raises(DatabaseError):
        interface.add_role_to_user('user', 'role')


def test_add_bun_class(interface):
    assert not interface.bun_class_exists('donut')
    interface.add_bun_class('donut', 1.0, 50.0)
    assert interface.bun_class_exists('donut')
    assert 'donut' in interface.list_bun_classes()


def test_create_order(interface):
    assert not interface.active_order_exists()
    interface.create_order(expiry_date=HAS_NOT_EXPIRED)
    assert interface.active_order_exists()
    assert not interface.current_order_is_expired()


def test_create_order_exists(interface):
    interface.create_order(expiry_date=HAS_NOT_EXPIRED)
    with pytest.raises(DatabaseError):
        interface.create_order(expiry_date=HAS_NOT_EXPIRED)


def test_no_order_exists(interface):
    with pytest.raises(DatabaseError):
        interface.current_order_is_expired()


def test_create_order_expired(interface):
    assert not interface.active_order_exists()
    with pytest.raises(DatabaseError):
        interface.create_order(expiry_date=HAS_EXPIRED)


def test_drop_order_current(interface):
    assert not interface.active_order_exists()
    interface.create_order(expiry_date=HAS_NOT_EXPIRED)
    assert interface.active_order_exists()
    interface.drop_current_order()
    assert not interface.active_order_exists()


def test_expire_order(interface):
    assert interface.get_balance('user') == 0.0
    interface.create_order(HAS_NOT_EXPIRED)
    interface.order_bun('user', 'Weizen')
    interface.process_order()
    assert interface.get_balance('user') == -1.0


def test_get_balance(interface):
    assert interface.get_balance('user') == 0.0
    assert interface.get_balance('non-existent') is None


def test_change_balance(interface):
    assert interface.get_balance('user') == 0.0
    interface.change_balance('user', 1.0, 'user')
    assert interface.get_balance('user') == 1.0


def test_list_accounts(interface, app):
    assert interface.list_accounts() == ['user']
    with app.app.app_context():
        interface.create_user('foo', 'foo')
    assert interface.list_accounts() == ['foo', 'user']


def test_password_is_correct(interface, app):
    with app.app.app_context():
        assert interface.password_is_correct('user', 'user')
        assert not interface.password_is_correct('user', 'foo')
