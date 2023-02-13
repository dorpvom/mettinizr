import pytest
from test.unit.common import TestUser


@pytest.fixture(scope='function', autouse=True)
def patch_current_user(monkeypatch):
    monkeypatch.setattr('app.dashboard.current_user', TestUser())


def test_home_dashboard(client, app):
    response = client.get('/')
    assert 'Hi {}'.format(TestUser.name).encode() in response.data
    assert b'There is no current order!' in response.data


def test_dashboard_order_exists(client, app):
    app.database.create_order('2099-01-01')

    response = client.get('/')
    assert 'Hi {}'.format(TestUser.name).encode() in response.data
    assert b'There is no current order!' not in response.data


def test_dashboard_order_history(client, app):
    app.database.create_order('2099-01-01')
    app.database.order_bun(TestUser.name, 'Weizen')
    app.database.process_order()

    response = client.get('/')
    assert b'You have ordered a mean of 1.0 total buns' in response.data
