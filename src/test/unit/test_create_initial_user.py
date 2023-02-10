from create_initial_user import create_init_user


def test_create_init_user(combined_app):
    create_init_user(combined_app)

    assert combined_app.user_interface.user_exists('init')
    assert combined_app.user_interface.role_exists('admin')
    assert combined_app.user_interface.role_exists('user')

    user = combined_app.user_interface.find_user('init')
    assert user
    assert len(user.roles) == 1
