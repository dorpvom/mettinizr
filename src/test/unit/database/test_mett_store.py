'''
account: id, name, balance (name private_key)
order: id, processed, orders, expiry_date (orders list of (account, bun), with account foreign_key on account.id and bun foreign_key on price.id)
buns: id, bun_class, price, mett
purchase: id, account, price, purpose, processed (account foreign_key on accound.name)
'''
import pytest

from test.unit.common import config_for_tests, HAS_NOT_EXPIRED, HAS_EXPIRED
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


def test_create_account(mock_store):
    assert mock_store._account.count_documents({'name': 'account_test'}) == 0
    mock_store.create_account('account_test')
    assert mock_store._account.count_documents({'name': 'account_test'}) == 1
    with pytest.raises(StorageException):
        mock_store.create_account('account_test')


def test_delete_account(mock_store):
    mock_store._account.insert_one({'name': 'test_account', 'balance': 0.0})
    assert mock_store.delete_account('test_account') == 1

    with pytest.raises(StorageException):
        mock_store.delete_account('test_account')


def test_account_exists(mock_store):
    assert not mock_store.account_exists('account_test')
    mock_store._account.insert_one({'name': 'account_test', 'balance': 5.0})
    assert mock_store.account_exists('account_test')


def test_get_account_information(mock_store):
    with pytest.raises(StorageException):
        mock_store.get_account_information('account_test')

    account_id = mock_store._account.insert_one({'name': 'account_test', 'balance': 5.0}).inserted_id
    account_information = mock_store.get_account_information('account_test')

    assert account_information == {'name': 'account_test', 'balance': 5.0, '_id': str(account_id)}


def test_resolve_account(mock_store):
    with pytest.raises(StorageException):
        assert mock_store._get_account_name_from_id('some_id')

    with pytest.raises(StorageException):
        assert mock_store._get_account_id_from_name('account_test')

    account_id = mock_store._account.insert_one({'name': 'account_test', 'balance': 0.0}).inserted_id

    assert mock_store._get_account_name_from_id(account_id) == 'account_test'
    assert mock_store._get_account_id_from_name('account_test') == account_id


def test_resolve_bun(mock_store):
    bun_id = mock_store._resolve_bun('Roggen')

    assert mock_store._resolve_bun(bun_id) == 'Roggen'
    assert mock_store._buns.find_one({'bun_class': 'Roggen'})['_id'] == bun_id


def test_create_order(mock_store):
    order_id = mock_store.create_order(HAS_NOT_EXPIRED)
    assert order_id

    with pytest.raises(StorageException):
        mock_store.create_order(HAS_NOT_EXPIRED)

    mock_store._order.delete_one({'_id': order_id})
    assert mock_store.create_order(HAS_NOT_EXPIRED)


def test_create_order_expired_fails(mock_store):
    with pytest.raises(StorageException):
        mock_store.create_order(HAS_EXPIRED)


def test_active_order_exists(mock_store):
    assert not mock_store.active_order_exists()
    mock_store._order.insert_one({'orders': [], 'processed': False, 'expiry_date': HAS_NOT_EXPIRED})
    assert mock_store.active_order_exists()


def test_expire_order(mock_store):
    mock_store._account.insert_one({'name': 'test', 'balance': 5.0})
    mock_store.create_order(HAS_NOT_EXPIRED)
    mock_store.order_bun('test', 'Weizen')
    mock_store.process_order()
    assert mock_store._account.find_one({'name': 'test'})['balance'] == 4.0


def test_drop_order_current(mock_store):
    order_id = mock_store._order.insert_one({'orders': [], 'processed': False, 'expiry_date': HAS_NOT_EXPIRED}).inserted_id

    assert mock_store._order.find_one({'_id': order_id})
    mock_store.drop_current_order()
    assert not mock_store._order.find_one({'_id': order_id})


def test_state_purchase(mock_store):
    mock_store._account.insert_one({'name': 'purchase_test', 'balance': 0.0})

    assert not mock_store._purchase.find_one({'purpose': 'absolution'})
    mock_store.state_purchase('purchase_test', 1.23, 'absolution')
    assert mock_store._purchase.find_one({'purpose': 'absolution'})


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


def test_list_purchases(mock_store):
    mock_store.create_account('test')
    purchase_id = mock_store._purchase.insert_one({'account': 'test', 'price': 1.23, 'purpose': 'any', 'processed': False}).inserted_id
    purchases = mock_store.list_purchases()
    assert len(purchases) == 1
    assert purchases[0]['_id'] == str(purchase_id) and purchases[0]['purpose'] == 'any'


def test_change_mett_formula(mock_store):
    assert mock_store._buns.find_one({'bun_class': 'Weizen'})['mett'] == 66.0
    mock_store.change_mett_formula('Weizen', 80.0)
    assert mock_store._buns.find_one({'bun_class': 'Weizen'})['mett'] == 80.0

    with pytest.raises(StorageException):
        mock_store.change_mett_formula('NoBun', 80.0)


def test_change_bun_price(mock_store):
    assert mock_store._buns.find_one({'bun_class': 'Weizen'})['price'] == 1.0
    mock_store.change_bun_price('Weizen', 1.5)
    assert mock_store._buns.find_one({'bun_class': 'Weizen'})['price'] == 1.5

    with pytest.raises(StorageException):
        mock_store.change_bun_price('NoBun', 1.5)


def test_assign_spare(mock_store):
    mock_store._account.insert_one({'name': 'test', 'balance': 2.0})
    mock_store.assign_spare('Weizen', 'test')
    assert mock_store._account.find_one({'name': 'test'})['balance'] == 1.0


def test_get_order(mock_store):
    with pytest.raises(StorageException):
        mock_store.get_current_bun_order()

    account_id_1 = mock_store._account.insert_one({'name': 'order_test_1', 'balance': 0.0}).inserted_id
    account_id_2 = mock_store._account.insert_one({'name': 'order_test_2', 'balance': 0.0}).inserted_id
    weizen_id = mock_store._buns.find_one({'bun_class': 'Weizen'})['_id']
    mock_store._order.insert_one({'orders': [(account_id_1, weizen_id), (account_id_2, weizen_id)], 'processed': False, 'expiry_date': HAS_NOT_EXPIRED})

    assert mock_store.get_current_user_buns('order_test_1') == {'Weizen': 1, 'Roggen': 0, 'Roeggelchen': 0}
    # 2 'Weizen' buns are added as spares
    assert mock_store.get_current_bun_order() == {'Weizen': 4, 'Roggen': 0, 'Roeggelchen': 0}
    assert mock_store.get_current_mett_order() == 4 * 66.0


def test_spares_with_roeggelchen(mock_store):
    account_id = mock_store._account.insert_one({'name': 'order_test', 'balance': 0.0}).inserted_id
    weizen_id = mock_store._buns.find_one({'bun_class': 'Weizen'})['_id']
    mock_store._order.insert_one({'orders': [(account_id, weizen_id)], 'processed': False, 'expiry_date': HAS_NOT_EXPIRED})

    assert mock_store.get_current_bun_order() == {'Weizen': 3, 'Roggen': 0, 'Roeggelchen': 0}
    mock_store.order_bun('order_test', 'Roeggelchen')
    assert mock_store.get_current_bun_order() == {'Weizen': 2, 'Roggen': 0, 'Roeggelchen': 2}


def test_order_history(mock_store):
    account_id = mock_store._account.insert_one({'name': 'order_test', 'balance': 0.0}).inserted_id
    weizen_id = mock_store._buns.find_one({'bun_class': 'Weizen'})['_id']
    roggen_id = mock_store._buns.find_one({'bun_class': 'Roggen'})['_id']
    mock_store._order.insert_one({'orders': [(account_id, weizen_id), (account_id, weizen_id), (account_id, roggen_id)], 'processed': True, 'expiry_date': '2000-01-01'})
    mock_store._order.insert_one({'orders': [(account_id, weizen_id), (account_id, roggen_id), (account_id, roggen_id)], 'processed': True, 'expiry_date': '2000-01-01'})

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
    mock_store._account.insert_one({'name': 'order_test', 'balance': 0.0}).inserted_id
    mock_store._order.insert_one({'orders': [], 'processed': False, 'expiry_date': HAS_EXPIRED})
    with pytest.raises(StorageException):
        mock_store.order_bun('order_test', 'Weizen')
