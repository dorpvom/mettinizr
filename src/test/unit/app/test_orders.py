import pytest
from test.unit.common import MockUser


@pytest.fixture(scope='function', autouse=True)
def patch_current_user(monkeypatch):
    monkeypatch.setattr('app.orders.current_user', MockUser())
    monkeypatch.setattr('app.dashboard.current_user', MockUser())


def test_order_home(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.name)
    response = mock_app.get('/order')
    assert b'State purchase' in response.data


def test_order_home_active(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.name)
    response = mock_app.get('/order')
    assert b'There is no current order!' in response.data

    app_fixture.mett_store.create_order('2099-01-01')
    response = mock_app.get('/order')
    assert b'There is no current order!' not in response.data
    assert b'132.0 g of mett' in response.data


def test_order_bun(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.name)
    app_fixture.mett_store.create_order('2099-01-01')
    response = mock_app.get('/order')
    assert b'132.0 g of mett' in response.data

    response = mock_app.post('/order', data={'orderAmount': 1, 'orderClass': 'Weizen'}, follow_redirects=True)
    assert b'There is no current order!' not in response.data

    response = mock_app.get('/order')
    assert b'198.0 g of mett' in response.data


def test_show_purpose_page(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.name)

    response = mock_app.get('/order/purchase')
    assert b'Purpose of purchase' in response.data


def test_state_purchase(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.name)
    assert not app_fixture.mett_store.list_purchases()

    response = mock_app.post('/order/purchase', data={'amount': 7.32, 'purpose': 'For testing'})
    assert response.status_code == 200

    purchases = app_fixture.mett_store.list_purchases()
    assert purchases
    assert purchases[0]['price'] == 7.32


def test_previous_orders(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.name)
    app_fixture.mett_store.create_order('2099-01-01')
    mock_app.post('/order', data={'orderAmount': 1, 'orderClass': 'Weizen'})

    assert '<li>{}: '.format(MockUser.name) in mock_app.get('/order/previous').data.decode()
