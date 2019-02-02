from test.unit.common import MockUser


def test_user_home(mock_app, app_fixture):
    app_fixture.user_interface.create_role(name='test_role')
    app_fixture.user_interface.add_role_to_user(user=app_fixture.user_interface.find_user(email=MockUser.email), role='test_role')
    app_fixture.mett_store.create_account(MockUser.email)
    response = mock_app.get('/user')
    assert response.status_code == 200
    assert MockUser.email.encode() in response.data
