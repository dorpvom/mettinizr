import sys

from app.app_setup import AppSetup


def create_init_user(app_setup):
    app_setup.mett_store.create_account('init')

    with app_setup.app.app_context():
        app_setup.user_interface.create_user(name='init', password='init')
    app_setup.user_interface.create_role(name='admin')
    app_setup.user_interface.create_role(name='user')
    app_setup.user_interface.add_role_to_user(user='init', role='admin')

    return 0


if __name__ == '__main__':
    sys.exit(create_init_user(AppSetup()))
