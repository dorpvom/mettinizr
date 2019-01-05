'''
account: id, name, balance (name private_key)
order: id, expired, orders (orders list of (account, bun), with account foreign_key on account.id and bun foreign_key on price.id)
buns: id, bun_class, price, mett
purchase: id, account, price, purpose, processed (account foreign_key on accound.name)
'''
import pytest

from test.unit.common import config_for_tests
from database.mett_store import MettStore, StorageException
from mongomock import MongoClient


@pytest.fixture(scope='function')
def mock_store(monkeypatch):
    monkeypatch.setattr('database.mett_store.MongoClient', MongoClient)
    return MettStore(config=config_for_tests())


def test_book_money(mock_store):
    mock_store._account.insert_one({'name': 'test', 'balance': 0.0})
    mock_store.book_money('test', 10.0)
    assert mock_store._account.find_one({'name': 'test'})['balance'] == 10.0
    mock_store.book_money('test', 3.3)
    assert mock_store._account.find_one({'name': 'test'})['balance'] == 13.3


def test_list_accounts(mock_store):
    assert mock_store.list_accounts() == []

    _id1 = mock_store._account.insert_one({'name': 'test_one', 'balance': -12.2}).inserted_id
    _id2 = mock_store._account.insert_one({'name': 'test_two', 'balance': 6.3}).inserted_id

    assert mock_store.list_accounts() == [(_id1, 'test_one'), (_id2, 'test_two')]


def test_create_order(mock_store):
    order_id = mock_store.create_order()
    assert order_id

    with pytest.raises(StorageException):
        mock_store.create_order()

    mock_store._order.delete_one({'_id': order_id})
    assert mock_store.create_order()


def test_create_account(mock_store):
    assert mock_store._account.count_documents({'name': 'account_test'}) == 0
    mock_store.create_account('account_test')
    assert mock_store._account.count_documents({'name': 'account_test'}) == 1
    with pytest.raises(StorageException):
        mock_store.create_account('account_test')


def test_expire_order(mock_store):
    mock_store._account.insert_one({'name': 'test', 'balance': 5.0})
    mock_store.create_order()
    mock_store.order_bun('test', 'Weizen')
    mock_store.expire_order()
    assert mock_store._account.find_one({'name': 'test'})['balance'] == 4.0


def test_drop_order_current(mock_store):
    order_id = mock_store._order.insert_one({'orders': [], 'expired': False}).inserted_id

    assert mock_store._order.find_one({'_id': order_id})
    mock_store.drop_order()
    assert not mock_store._order.find_one({'_id': order_id})


def test_drop_order_id(mock_store):
    order_id_one = mock_store._order.insert_one({'orders': [], 'expired': True}).inserted_id
    order_id_two = mock_store._order.insert_one({'orders': [], 'expired': False}).inserted_id

    assert mock_store._order.find_one({'_id': order_id_one})
    assert mock_store._order.find_one({'_id': order_id_two})
    mock_store.drop_order(order_id_one)

    assert not mock_store._order.find_one({'_id': order_id_one})
    assert mock_store._order.find_one({'_id': order_id_two})


def test_authorize_purchase(mock_store):
    mock_store.create_account('test')
    purchase_id = mock_store._purchase.insert_one({'account': 'test', 'price': 1.23, 'purpose': 'any', 'processed': False}).inserted_id
    mock_store.authorize_purchase(purchase_id)
    assert mock_store._purchase.find_one({'_id': purchase_id})['processed']
    assert mock_store._account.find_one({'name': 'test'})['balance'] == 1.23


def test_decline_purchase(mock_store):
    mock_store.create_account('test')
    purchase_id = mock_store._purchase.insert_one({'account': 'test', 'price': 1.23, 'purpose': 'any', 'processed': False}).inserted_id
    mock_store.decline_purchase(purchase_id)
    assert mock_store._purchase.find_one({'_id': purchase_id})['processed']
    assert mock_store._account.find_one({'name': 'test'})['balance'] == 0.0
