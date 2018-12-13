'''
account: id, name, balance (id private_key)
order: id, expired, orders (orders list of (account, bun), with account foreign_key on account.id and bun foreign_key on price.id)
price: id, bun_class, amount
purchase: id, account, amount, processed (account foreign_key on accound.id)
mett_formula: bun, amount (bun foreign_key on price.id)
'''
import pytest

from database.mett_store import MettStore, StorageException
from mongomock import MongoClient


@pytest.fixture(scope='function')
def mock_store(monkeypatch):
    monkeypatch.setattr('database.mett_store.MongoClient', MongoClient)
    return MettStore()


def test_book_money(mock_store):
    _id = mock_store._account.insert_one({'name': 'test', 'balance': 0.0}).inserted_id
    mock_store.book_money(_id, 10.0)
    assert mock_store._account.find_one({'name': 'test'})['balance'] == 10.0
    mock_store.book_money(_id, 3.3)
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
