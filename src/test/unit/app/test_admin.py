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
