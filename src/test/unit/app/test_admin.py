from test.unit.common import TestUser, HAS_EXPIRED, HAS_NOT_EXPIRED


def test_admin_home(client, app):
    response = client.get('/admin')
    assert b'Create order' in response.data

    app.database.create_order(HAS_NOT_EXPIRED)

    response = client.get('/admin')
    assert b'Close order' in response.data


def test_increase_balance(client, app, monkeypatch):
    monkeypatch.setattr('app.admin.current_user', TestUser())

    response = client.get('/admin/balance')
    assert TestUser.name.encode() in response.data
    assert app.database.get_balance(TestUser.name) == 0.0

    response = client.post('/admin/balance', data={'username': TestUser.name, 'added': 1.37})
    assert response.status_code == 200
    assert app.database.get_balance(TestUser.name) == 1.37


def test_decrease_balance(client, app, monkeypatch):
    monkeypatch.setattr('app.admin.current_user', TestUser())

    response = client.get('/admin/balance')
    assert TestUser.name.encode() in response.data
    assert app.database.get_balance(TestUser.name) == 0.0

    response = client.post('/admin/balance', data={'username': TestUser.name, 'removed': 1.37})
    assert response.status_code == 200
    assert app.database.get_balance(TestUser.name) == -1.37


def test_create_order_expired(client, app):
    response = client.post('/admin', data={'expiry': HAS_EXPIRED})
    assert response.status_code == 200
    assert 'enter date that has' in response.data.decode()


def test_create_order_exists(client, app):
    app.database.create_order(HAS_NOT_EXPIRED)
    response = client.post('/admin', data={'expiry': HAS_NOT_EXPIRED})
    assert response.status_code == 200
    assert b'while another one is active' in response.data


def test_create_order_success(client, app):
    response = client.post('/admin', data={'expiry': HAS_NOT_EXPIRED})
    assert response.status_code == 200
    assert not 'enter date that has' in response.data.decode()
    assert app.database.active_order_exists()


def test_close_order(client, app):
    app.database.create_order(HAS_NOT_EXPIRED)

    assert app.database.active_order_exists()
    response = client.get('/admin/close_order')
    assert response.status_code == 200
    assert not app.database.active_order_exists()


def test_cancel_order(client, app):
    app.database.create_order(HAS_NOT_EXPIRED)

    assert app.database.active_order_exists()
    response = client.get('/admin/cancel_order')
    assert response.status_code == 200
    assert not app.database.active_order_exists()


def test_change_mett_formula(client, app):
    assert app.database.list_bun_classes_with_price()['Weizen'] == 1.0
    response = client.post('/admin/formula', data={'price': 2.0, 'bun': 'Weizen'})
    assert response.status_code == 200
    assert app.database.list_bun_classes_with_price()['Weizen'] == 2.0

    assert app.database.list_bun_classes_with_mett()['Weizen'] == 66.0
    response = client.post('/admin/formula', data={'amount': 80.0, 'bun': 'Weizen'})
    assert response.status_code == 200
    assert app.database.list_bun_classes_with_mett()['Weizen'] == 80.0

    response = client.post('/admin/formula', data={})
    assert b'Empty request' in response.data


def test_show_spare_page(client):
    response = client.get('/admin/spare')
    assert response.status_code == 200
    assert b'Weizen' in response.data


def test_assign_spare(client, app):
    app.database.change_balance(TestUser.name, 10.0, TestUser.name)
    assert app.database.get_balance(TestUser.name) == 10.0

    response = client.post('/admin/spare', data={'bun': 'Weizen', 'username': TestUser.name})
    assert response.status_code == 200
    assert app.database.get_balance(TestUser.name) == 9.0


def test_list_purchases(client, app):
    app.database.state_purchase(TestUser.name, 1.23, 'testing purposes')

    response = client.get('/admin/purchase')
    assert b'testing purposes' in response.data


def test_decline_purchase(client, app, monkeypatch):
    monkeypatch.setattr('app.admin.current_user', TestUser())
    app.database.state_purchase(TestUser.name, 1.23, 'testing purposes')
    purchase = app.database.list_purchases()[0]

    assert app.database.get_balance(TestUser.name) == 0.0
    response = client.get('/admin/purchase/decline/{}'.format(purchase.p_id))
    assert response.status_code == 200
    assert app.database.get_balance(TestUser.name) == 0.0
    assert b'table-danger' in client.get('/admin/purchase').data
    assert b'table-success' not in client.get('/admin/purchase').data


def test_authorize_purchase(client, app, monkeypatch):
    monkeypatch.setattr('app.admin.current_user', TestUser())
    app.database.state_purchase(TestUser.name, 1.23, 'testing purposes')
    purchase = app.database.list_purchases()[0]

    assert app.database.get_balance(TestUser.name) == 0.0
    response = client.get('/admin/purchase/authorize/{}'.format(purchase.p_id))
    assert response.status_code == 200
    assert app.database.get_balance(TestUser.name) == 1.23
    assert b'table-success' in client.get('/admin/purchase').data
    assert b'table-danger' not in client.get('/admin/purchase').data
