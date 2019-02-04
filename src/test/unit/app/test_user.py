from test.unit.common import MockUser, simple_session


def test_user_home(mock_app, app_fixture):
    with simple_session(app_fixture.user_database):
        app_fixture.user_interface.create_role(name='test_role')
        app_fixture.user_interface.add_role_to_user(user=app_fixture.user_interface.find_user(email=MockUser.email), role='test_role')

    app_fixture.mett_store.create_account(MockUser.email)

    response = mock_app.get('/user')

    assert response.status_code == 200
    assert MockUser.email.encode() in response.data
    assert b'test_role' in response.data


def test_create_user(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.email)
    response = mock_app.post('/user', data={'new_user': 'a_user', 'new_password': 'a_password'})
    assert b'a_user' in response.data


def test_add_role(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.email)

    with simple_session(app_fixture.user_database):
        app_fixture.user_interface.create_role(name='test_role')

    before = mock_app.get('/user')
    assert b'<td>test_role</td>' not in before.data

    after = mock_app.post('/user', data={'add_role_username': MockUser.email, 'added_role': 'test_role'})
    assert b'<td>test_role</td>' in after.data


def test_remove_role(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.email)

    with simple_session(app_fixture.user_database):
        app_fixture.user_interface.create_role(name='test_role')
        app_fixture.user_interface.add_role_to_user(user=app_fixture.user_interface.find_user(email=MockUser.email), role='test_role')

    before = mock_app.get('/user')
    assert b'<td>test_role</td>' in before.data

    after = mock_app.post('/user', data={'remove_role_username': MockUser.email, 'removed_role': 'test_role'})
    assert b'<td>test_role</td>' not in after.data


def test_delete_user(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.email)

    assert app_fixture.mett_store.account_exists(MockUser.email)

    response = mock_app.get('/user/delete/{}'.format(MockUser.email))
    assert response.status_code == 200
    assert not app_fixture.mett_store.account_exists(MockUser.email)


def test_delete_non_existing_user(mock_app, app_fixture):
    response = mock_app.get('/user/delete/{}'.format('another'))
    assert b'another does not exist' in response.data

    app_fixture.mett_store.create_account('another')

    response = mock_app.get('/user/delete/{}'.format('another'))
    assert b'Failed to delete user' in response.data


def test_create_bad_password(mock_app, app_fixture):
    app_fixture.mett_store.create_account(MockUser.email)
    response = mock_app.post('/user', data={'new_user': 'a_user', 'new_password': ''})
    assert b'Please choose legal password' in response.data


def test_create_exists_already(mock_app, app_fixture):
    app_fixture.mett_store.create_account('a_user')
    response = mock_app.post('/user', data={'new_user': 'a_user', 'new_password': 'a_password'})
    assert b'a_user exists' in response.data

    response = mock_app.post('/user', data={'new_user': 'a_user', 'new_password': 'a_password'})
    assert b'user a_user. Might already exist' in response.data
