from test.unit.common import MockUser


def test_user_home(mock_app, app_fixture):
    app_fixture.user_interface.create_role(name='test_role')
    app_fixture.user_interface.add_role_to_user(user=MockUser.name, role='test_role')

    app_fixture.mett_store.create_account(MockUser.name)

    response = mock_app.get('/user')

    assert response.status_code == 200
    assert MockUser.name.encode() in response.data
    assert b'test_role' in response.data


def test_create_user(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.name)
    response = mock_app.post('/user', data={'new_user': 'a_user', 'new_password': 'a_password'})
    assert b'a_user' in response.data

    assert app_fixture.config.get('User', 'default_role').encode() in response.data


def test_add_role(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.name)

    app_fixture.user_interface.create_role(name='test_role')

    before = mock_app.get('/user')
    assert b'<td>test_role</td>' not in before.data

    after = mock_app.post('/user', data={'add_role_username': MockUser.name, 'added_role': 'test_role'})
    assert b'<td>test_role</td>' in after.data


def test_remove_role(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.name)

    app_fixture.user_interface.create_role(name='test_role')
    app_fixture.user_interface.add_role_to_user(user=MockUser.name, role='test_role')

    before = mock_app.get('/user')
    assert b'<td>test_role</td>' in before.data

    after = mock_app.post('/user', data={'remove_role_username': MockUser.name, 'removed_role': 'test_role'})
    assert b'<td>test_role</td>' not in after.data


def test_delete_user(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.name)

    assert app_fixture.mett_store.account_exists(MockUser.name)

    response = mock_app.get('/user/delete/{}'.format(MockUser.name), follow_redirects=True)
    assert response.status_code == 200
    assert not app_fixture.mett_store.account_exists(MockUser.name)


def test_delete_non_existing_user(mock_app, app_fixture):
    response = mock_app.get('/user/delete/{}'.format('another'), follow_redirects=True)
    assert b'No existing account another' in response.data


def test_delete_redirect_correct(mock_app, app_fixture):
    response = mock_app.get('/user/delete/{}'.format('another'))
    assert response.location == 'http://localhost/user'


def test_create_bad_password(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.name)
    response = mock_app.post('/user', data={'new_user': 'a_user', 'new_password': ''})
    assert b'Please choose legal password' in response.data


def test_create_exists_already(mock_app, app_fixture):
    app_fixture.mett_store.create_account('a_user')
    response = mock_app.post('/user', data={'new_user': 'a_user', 'new_password': 'a_password'})
    assert b'a_user exists' in response.data, 'Error should originate from mett store'

    response = mock_app.post('/user', data={'new_user': 'a_user', 'new_password': 'a_password'})
    assert b'User already exists' in response.data, 'Error should originate from user store'


def test_change_user_password(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.name)

    response = mock_app.post('/user', data={'name': MockUser.name, 'new_password': 'one_password', 'new_password_confirm': 'another_password'})
    assert b'password did not match' in response.data
    assert b'change successful' not in response.data

    response = mock_app.post('/user', data={'name': MockUser.name, 'new_password': 'same_password', 'new_password_confirm': 'same_password'})
    assert b'password did not match' not in response.data
    assert b'change successful' in response.data
