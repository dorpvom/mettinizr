'''
account: id, name, balance (name private_key)
order: id, processed, orders, expiry_date (orders list of (account, bun), with account foreign_key on account.id and bun foreign_key on price.id)
buns: id, bun_class, price, mett
purchase: id, account, price, purpose, processed (account foreign_key on accound.name)
'''
import pytest

from test.unit.common import HAS_NOT_EXPIRED, HAS_EXPIRED
from database.mett_store import MettStore, StorageException
from mongomock import MongoClient


@pytest.fixture(scope='function')
def mock_store(monkeypatch, config_for_tests):
    monkeypatch.setattr('database.mett_store.MongoClient', MongoClient)
    return MettStore(config=config_for_tests)


def test_book_money(mock_store):
    mock_store._account.insert_one({'name': 'test', 'balance': 0.0})
    mock_store._book_money('test', 10.0)
    assert mock_store._account.find_one({'name': 'test'})['balance'] == 10.0
    mock_store._book_money('test', 3.3)
    assert mock_store._account.find_one({'name': 'test'})['balance'] == 13.3


def test_drop_order_current(mock_store):
    order_id = mock_store._order.insert_one({'orders': [], 'processed': False, 'expiry_date': HAS_NOT_EXPIRED}).inserted_id

    assert mock_store._order.find_one({'_id': order_id})
    mock_store.drop_current_order()
    assert not mock_store._order.find_one({'_id': order_id})


def test_assign_spare(mock_store):
    mock_store._account.insert_one({'name': 'test', 'balance': 2.0})
    mock_store.assign_spare('Weizen', 'test')
    assert mock_store._account.find_one({'name': 'test'})['balance'] == 1.0


def test_get_order(mock_store):
    with pytest.raises(StorageException):
        mock_store.get_current_bun_order()

    mock_store._account.insert_one({'name': 'order_test_1', 'balance': 0.0})
    mock_store._account.insert_one({'name': 'order_test_2', 'balance': 0.0})
    mock_store._order.insert_one({'orders': [('order_test_1', 'Weizen'), ('order_test_2', 'Weizen')], 'processed': False, 'expiry_date': HAS_NOT_EXPIRED})

    assert mock_store.get_current_user_buns('order_test_1') == {'Weizen': 1, 'Roggen': 0, 'Roeggelchen': 0}
    assert mock_store.get_current_bun_order() == {'Weizen': 3, 'Roggen': 1, 'Roeggelchen': 0}
    assert mock_store.get_current_mett_order() == 4 * 66.0


def test_spares_with_roeggelchen(mock_store):
    mock_store._account.insert_one({'name': 'order_test', 'balance': 0.0})
    mock_store._order.insert_one({'orders': [('order_test', 'Weizen')], 'processed': False, 'expiry_date': HAS_NOT_EXPIRED})

    assert mock_store.get_current_bun_order() == {'Weizen': 2, 'Roggen': 1, 'Roeggelchen': 0}
    mock_store.order_bun('order_test', 'Roeggelchen')
    assert mock_store.get_current_bun_order() == {'Weizen': 2, 'Roggen': 0, 'Roeggelchen': 2}


def test_order_history(mock_store):
    mock_store._account.insert_one({'name': 'order_test', 'balance': 0.0})
    mock_store._order.insert_one({'orders': [('order_test', 'Weizen'), ('order_test', 'Weizen'), ('order_test', 'Roggen')], 'processed': True, 'expiry_date': '2000-01-01'})
    mock_store._order.insert_one({'orders': [('order_test', 'Weizen'), ('order_test', 'Roggen'), ('order_test', 'Roggen')], 'processed': True, 'expiry_date': '2000-01-01'})

    assert mock_store.get_order_history('order_test') == ({'Weizen': 1.5, 'Roggen': 1.5, 'Roeggelchen': 0}, 3)


def test_is_expired(mock_store):
    assert not mock_store._is_expired(HAS_NOT_EXPIRED)
    assert mock_store._is_expired(HAS_EXPIRED)


def test_current_order_is_expired(mock_store):
    mock_store._order.insert_one({'orders': [], 'processed': False, 'expiry_date': HAS_EXPIRED})
    assert mock_store.current_order_is_expired()
    mock_store._order.update_one({'expiry_date': HAS_EXPIRED}, {'$set': {'processed': True}})

    with pytest.raises(StorageException):
        mock_store.current_order_is_expired()

    mock_store._order.insert_one({'orders': [], 'processed': False, 'expiry_date': HAS_NOT_EXPIRED})
    assert not mock_store.current_order_is_expired()


def test_order_bun_expired_fails(mock_store):
    mock_store._account.insert_one({'name': 'order_test', 'balance': 0.0})
    mock_store._order.insert_one({'orders': [], 'processed': False, 'expiry_date': HAS_EXPIRED})
    with pytest.raises(StorageException):
        mock_store.order_bun('order_test', 'Weizen')
