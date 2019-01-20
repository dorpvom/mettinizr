import pytest
from test.unit.common import MockUser


@pytest.fixture(scope='function', autouse=True)
def patch_current_user(monkeypatch):
    monkeypatch.setattr('app.dashboard.current_user', MockUser())


def test_home_dashboard(mock_app, app_setup):
    app_setup.mett_store.create_account(MockUser.email)

    response = mock_app.get('/')
    assert 'Welcome {}!'.format(MockUser.email).encode() in response.data
    assert b'There is no current order!' in response.data


def test_dashboard_order_exists(mock_app, app_setup):
    app_setup.mett_store.create_account(MockUser.email)
    app_setup.mett_store.create_order()

    response = mock_app.get('/')
    assert 'Welcome {}!'.format(MockUser.email).encode() in response.data
    assert not b'There is no current order!' in response.data


def test_dashboard_order_history(mock_app, app_setup):
    app_setup.mett_store.create_account(MockUser.email)
    app_setup.mett_store.create_order()
    app_setup.mett_store.order_bun(MockUser.email, 'Weizen')
    app_setup.mett_store.expire_order()

    response = mock_app.get('/')
    assert b'You have ordered a mean of 1.0 buns' in response.data
