from flask_security import Security

from database.user_store import UserRoleDatabase


def add_flask_security_to_app(app, config):
    _add_configuration_to_app(app, config)

    user_interface = create_user_interface(config)
    _ = Security(app, user_interface)

    return user_interface


def create_user_interface(config):
    return UserRoleDatabase(config)


def _add_configuration_to_app(app, config):
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECURITY_PASSWORD_SALT'] = b'Salt'
    app.config['SQLALCHEMY_DATABASE_URI'] = config.get('Runtime', 'user_database', fallback='sqlite:///')
    app.config['SECURITY_UNAUTHORIZED_VIEW'] = '/login'
    app.config['LOGIN_DISABLED'] = config.getboolean('Runtime', 'testing')
