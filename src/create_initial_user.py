import sys

from app.app_setup import AppSetup


def create_init_user(app_setup):
    app_setup.database.create_tables()
    app_setup.database.initialize_bun_classes()

    with app_setup.app.app_context():
        app_setup.database.create_user(
            name=app_setup.config.get('Database', 'default_user'),
            password=app_setup.config.get('Database', 'default_password')
        )
    app_setup.database.create_role(name='admin')
    app_setup.database.create_role(name='user')
    app_setup.database.add_role_to_user(user=app_setup.config.get('Database', 'default_user'), role='admin')

    return 0


if __name__ == '__main__':
    sys.exit(create_init_user(AppSetup()))
