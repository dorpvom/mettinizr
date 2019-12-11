from test.unit.common import MockUser, HAS_EXPIRED, HAS_NOT_EXPIRED


def test_admin_home(mock_app, app_fixture):
    response = mock_app.get('/admin')
    assert b'Create order' in response.data

    app_fixture.mett_store.create_order(HAS_NOT_EXPIRED)

    response = mock_app.get('/admin')
    assert b'Close order' in response.data


def test_increase_balance(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.email)

    response = mock_app.get('/admin/balance')
    assert MockUser.email.encode() in response.data
    assert app_fixture.mett_store.get_account_information(MockUser.email)['balance'] == 0.0

    response = mock_app.post('/admin/balance', data={'username': MockUser.email, 'added': 1.37})
    assert response.status_code == 200
    assert app_fixture.mett_store.get_account_information(MockUser.email)['balance'] == 1.37


def test_decrease_balance(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.email)

    response = mock_app.get('/admin/balance')
    assert MockUser.email.encode() in response.data
    assert app_fixture.mett_store.get_account_information(MockUser.email)['balance'] == 0.0

    response = mock_app.post('/admin/balance', data={'username': MockUser.email, 'removed': 1.37})
    assert response.status_code == 200
    assert app_fixture.mett_store.get_account_information(MockUser.email)['balance'] == -1.37


def test_create_order_expired(mock_app, app_fixture):
    response = mock_app.post('/admin', data={'expiry': HAS_EXPIRED})
    assert response.status_code == 200
    assert 'enter date that has' in response.data.decode()


def test_create_order_exists(mock_app, app_fixture):
    app_fixture.mett_store.create_order(HAS_NOT_EXPIRED)
    response = mock_app.post('/admin', data={'expiry': HAS_NOT_EXPIRED})
    assert response.status_code == 200
    assert b'while another one is active' in response.data


def test_create_order_success(mock_app, app_fixture):
    response = mock_app.post('/admin', data={'expiry': HAS_NOT_EXPIRED})
    assert response.status_code == 200
    assert not 'enter date that has' in response.data.decode()
    assert app_fixture.mett_store.active_order_exists()


def test_close_order(mock_app, app_fixture):
    app_fixture.mett_store.create_order(HAS_NOT_EXPIRED)

    assert app_fixture.mett_store.active_order_exists()
    response = mock_app.get('/admin/close_order')
    assert response.status_code == 200
    assert not app_fixture.mett_store.active_order_exists()


def test_cancel_order(mock_app, app_fixture):
    app_fixture.mett_store.create_order(HAS_NOT_EXPIRED)

    assert app_fixture.mett_store.active_order_exists()
    response = mock_app.get('/admin/cancel_order')
    assert response.status_code == 200
    assert not app_fixture.mett_store.active_order_exists()


def test_change_mett_formula(mock_app, app_fixture):
    assert app_fixture.mett_store._buns.find_one({'bun_class': 'Weizen'})['price'] == 1.0
    response = mock_app.post('/admin/formula', data={'price': 2.0, 'bun': 'Weizen'})
    assert response.status_code == 200
    assert app_fixture.mett_store._buns.find_one({'bun_class': 'Weizen'})['price'] == 2.0

    assert app_fixture.mett_store._buns.find_one({'bun_class': 'Weizen'})['mett'] == 66.0
    response = mock_app.post('/admin/formula', data={'amount': 80.0, 'bun': 'Weizen'})
    assert response.status_code == 200
    assert app_fixture.mett_store._buns.find_one({'bun_class': 'Weizen'})['mett'] == 80.0

    response = mock_app.post('/admin/formula', data={})
    assert b'Empty request' in response.data


def test_show_spare_page(mock_app):
    response = mock_app.get('/admin/spare')
    assert response.status_code == 200
    assert b'Weizen' in response.data


def test_assign_spare(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.email)
    app_fixture.mett_store.book_money(MockUser.email, 10.0)
    assert app_fixture.mett_store.get_account_information(MockUser.email)['balance'] == 10.0

    response = mock_app.post('/admin/spare', data={'bun': 'Weizen', 'username': MockUser.email})
    assert response.status_code == 200
    assert app_fixture.mett_store.get_account_information(MockUser.email)['balance'] == 9.0


def test_list_purchases(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.email)
    app_fixture.mett_store.state_purchase(MockUser.email, 1.23, 'testing purposes')

    response = mock_app.get('/admin/purchase')
    assert b'testing purposes' in response.data


def test_decline_purchase(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.email)
    purchase_id = app_fixture.mett_store.state_purchase(MockUser.email, 1.23, 'testing purposes')

    assert app_fixture.mett_store.get_account_information(MockUser.email)['balance'] == 0.0
    response = mock_app.get('/admin/purchase/decline/{}'.format(purchase_id))
    assert response.status_code == 200
    assert app_fixture.mett_store.get_account_information(MockUser.email)['balance'] == 0.0
    assert b'testing purpose' not in mock_app.get('/admin/purchase').data


def test_authorize_purchase(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.email)
    purchase_id = app_fixture.mett_store.state_purchase(MockUser.email, 1.23, 'testing purposes')

    assert app_fixture.mett_store.get_account_information(MockUser.email)['balance'] == 0.0
    response = mock_app.get('/admin/purchase/authorize/{}'.format(purchase_id))
    assert response.status_code == 200
    assert app_fixture.mett_store.get_account_information(MockUser.email)['balance'] == 1.23
    assert b'testing purpose' not in mock_app.get('/admin/purchase').data
