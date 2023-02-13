import pytest
from test.unit.common import TestUser


@pytest.fixture(scope='function', autouse=True)
def patch_current_user(monkeypatch):
    monkeypatch.setattr('app.orders.current_user', TestUser())
    monkeypatch.setattr('app.dashboard.current_user', TestUser())


def test_order_home(client, app):
    response = client.get('/order')
    assert b'State purchase' in response.data


def test_order_home_active(client, app):
    response = client.get('/order')
    assert b'There is no current order!' in response.data

    app.database.create_order('2099-01-01')
    response = client.get('/order')
    assert b'There is no current order!' not in response.data
    assert b'132.0 g of mett' in response.data


def test_order_bun(client, app):
    app.database.create_order('2099-01-01')
    response = client.get('/order')
    # assert b'132.0 g of mett' in response.data

    response = client.post('/order', data={'orderAmount': 1, 'orderClass': 'Weizen'}, follow_redirects=True)
    assert b'There is no current order!' not in response.data

    response = client.get('/order')
    assert b'198.0 g of mett' in response.data


def test_show_purpose_page(client, app):
    response = client.get('/order/purchase')
    assert b'Purpose of purchase' in response.data


def test_state_purchase(client, app):
    assert not app.database.list_purchases()

    response = client.post('/order/purchase', data={'amount': 7.32, 'purpose': 'For testing'})
    assert response.status_code == 200

    purchases = app.database.list_purchases()
    assert purchases
    assert purchases[0].price == 7.32


def test_previous_orders(client, app):
    app.database.create_order('2099-01-01')
    client.post('/order', data={'orderAmount': 1, 'orderClass': 'Weizen'})

    assert '<li>{}: '.format(TestUser.name) in client.get('/order/previous').data.decode()
