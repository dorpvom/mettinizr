import pytest

from test.unit.common import TestUser


def test_user_home(client, app):
    app.database.create_role(name='test_role')
    app.database.add_role_to_user(user=TestUser.name, role='test_role')

    response = client.get('/user')

    assert response.status_code == 200
    assert TestUser.name.encode() in response.data
    assert b'test_role' in response.data


def test_create_user(client, app):
    response = client.post('/user', data={'new_user': 'a_user', 'new_password': 'a_password'})
    assert b'a_user' in response.data

    assert app.config.get('User', 'default_role').encode() in response.data


def test_add_role(client, app):
    app.database.create_role(name='test_role')

    before = client.get('/user')
    assert b'<td>test_role</td>' not in before.data

    after = client.post('/user', data={'add_role_username': TestUser.name, 'added_role': 'test_role'})
    assert b'<td>test_role</td>' in after.data


def test_remove_role(client, app):
    app.database.create_role(name='test_role')
    app.database.add_role_to_user(user=TestUser.name, role='test_role')

    before = client.get('/user')
    assert b'<td>test_role</td>' in before.data

    after = client.post('/user', data={'remove_role_username': TestUser.name, 'removed_role': 'test_role'})
    assert b'<td>test_role</td>' not in after.data


def test_delete_user(client, app, monkeypatch):
    monkeypatch.setattr('app.user.current_user', TestUser())

    assert app.database.user_exists(TestUser.name)

    response = client.get('/user/delete/{}'.format(TestUser.name), follow_redirects=True)
    assert response.status_code == 200
    assert not app.database.user_exists(TestUser.name)


@pytest.mark.skip(
    reason=('Reconsider this test. Either endpoint has to be rewritten or we can drop test since condition can never be'
            'reached anyway'
            )
)
def test_delete_non_existing_user(client, app):
    response = client.get('/user/delete/another', follow_redirects=True)
    assert b'No existing account another' in response.data


@pytest.mark.skip(
    reason=('Reconsider this test. Either endpoint has to be rewritten or we can drop test since condition can never be'
            'reached anyway'
            )
)
def test_delete_redirect_correct(client, app):
    response = client.get(f'/user/delete/another')
    assert response.location == 'http://localhost/user'


def test_create_bad_password(client, app):
    response = client.post('/user', data={'new_user': 'a_user', 'new_password': ''})
    assert b'Please choose legal password' in response.data


def test_create_exists_already(client, app):
    response = client.post('/user', data={'new_user': 'user', 'new_password': 'a_password'})
    assert b'User already exists' in response.data, 'Error should originate from user store'


def test_change_user_password(client, app):
    response = client.post('/user', data={'name': TestUser.name, 'new_password': 'one_password', 'new_password_confirm': 'another_password'})
    assert b'password did not match' in response.data
    assert b'change successful' not in response.data

    response = client.post('/user', data={'name': TestUser.name, 'new_password': 'same_password', 'new_password_confirm': 'same_password'})
    assert b'password did not match' not in response.data
    assert b'change successful' in response.data
