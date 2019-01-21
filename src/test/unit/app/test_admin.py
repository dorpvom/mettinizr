from test.unit.common import MockUser


def test_admin_home(mock_app, app_setup):
    response = mock_app.get('/admin')
    assert b'Create order' in response.data

    app_setup.mett_store.create_order()

    response = mock_app.get('/admin')
    assert b'Close order' in response.data


def test_book_money(mock_app, app_setup):
    app_setup.mett_store.create_account(MockUser.email)

    response = mock_app.get('/admin/balance')
    assert MockUser.email.encode() in response.data
    assert app_setup.mett_store.get_account_information(MockUser.email)['balance'] == 0.0

    response = mock_app.post('/admin/balance', data={'username': MockUser.email, 'amount': 1.37})
    assert response.status_code == 200
    assert app_setup.mett_store.get_account_information(MockUser.email)['balance'] == 1.37


def test_create_order(mock_app, app_setup):
    assert not app_setup.mett_store.active_order_exists()
    response = mock_app.get('/admin/create_order')
    assert response.status_code == 200
    assert app_setup.mett_store.active_order_exists()


def test_close_order(mock_app, app_setup):
    app_setup.mett_store.create_order()

    assert app_setup.mett_store.active_order_exists()
    response = mock_app.get('/admin/close_order')
    assert response.status_code == 200
    assert not app_setup.mett_store.active_order_exists()


def test_cancel_order(mock_app, app_setup):
    app_setup.mett_store.create_order()

    assert app_setup.mett_store.active_order_exists()
    response = mock_app.get('/admin/cancel_order')
    assert response.status_code == 200
    assert not app_setup.mett_store.active_order_exists()


def test_change_mett_formula(mock_app, app_setup):
    assert app_setup.mett_store._buns.find_one({'bun_class': 'Weizen'})['price'] == 1.0
    response = mock_app.post('/admin/formula', data={'price': 2.0, 'bun': 'Weizen'})
    assert response.status_code == 200
    assert app_setup.mett_store._buns.find_one({'bun_class': 'Weizen'})['price'] == 2.0

    assert app_setup.mett_store._buns.find_one({'bun_class': 'Weizen'})['mett'] == 66.0
    response = mock_app.post('/admin/formula', data={'amount': 80.0, 'bun': 'Weizen'})
    assert response.status_code == 200
    assert app_setup.mett_store._buns.find_one({'bun_class': 'Weizen'})['mett'] == 80.0


def test_assign_spare(mock_app, app_setup):
    app_setup.mett_store.create_account(MockUser.email)
    app_setup.mett_store.book_money(MockUser.email, 10.0)
    assert app_setup.mett_store.get_account_information(MockUser.email)['balance'] == 10.0

    response = mock_app.post('/admin/spare', data={'bun': 'Weizen', 'username': MockUser.email})
    assert response.status_code == 200
    assert app_setup.mett_store.get_account_information(MockUser.email)['balance'] == 9.0
