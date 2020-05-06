import pytest
from test.unit.common import MockUser


@pytest.fixture(scope='function', autouse=True)
def patch_current_user(monkeypatch):
    monkeypatch.setattr('app.dashboard.current_user', MockUser())


def test_home_dashboard(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.name)

    response = mock_app.get('/')
    assert 'Hi {}'.format(MockUser.name).encode() in response.data
    assert b'There is no current order!' in response.data


def test_dashboard_order_exists(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.name)
    app_fixture.mett_store.create_order('2099-01-01')

    response = mock_app.get('/')
    assert 'Hi {}'.format(MockUser.name).encode() in response.data
    assert b'There is no current order!' not in response.data


def test_dashboard_order_history(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.name)
    app_fixture.mett_store.create_order('2099-01-01')
    app_fixture.mett_store.order_bun(MockUser.name, 'Weizen')
    app_fixture.mett_store.process_order()

    response = mock_app.get('/')
    assert b'You have ordered a mean of 1.0 total buns' in response.data
