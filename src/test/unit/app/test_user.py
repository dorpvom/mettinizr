from test.unit.common import MockUser


def test_user_home(mock_app, app_fixture):
    # app_fixture.user_interface.create_user(email=MockUser.email, password=MockUser.password)
    response = mock_app.get('/user')
    assert response.status_code == 200
    assert MockUser.email.encode() in response.data
