from flask_security import Security, UserMixin, RoleMixin
from flask_sqlalchemy import SQLAlchemy

from database.user_store import UserRoleDatabase


def add_flask_security_to_app(app, config):
    _add_configuration_to_app(app, config)

    database = SQLAlchemy(app)

    user_interface = create_user_interface(database)
    _ = Security(app, user_interface)

    return database, user_interface


def create_user_interface(database):
    roles_users = database.Table('roles_users', database.Column('user_id', database.Integer(), database.ForeignKey('user.id')), database.Column('role_id', database.Integer(), database.ForeignKey('role.id')))

    class Role(database.Model, RoleMixin):
        id = database.Column(database.Integer(), primary_key=True)  # pylint: disable=invalid-name
        name = database.Column(database.String(80), unique=True)
        description = database.Column(database.String(255))

    class User(database.Model, UserMixin):
        id = database.Column(database.Integer, primary_key=True)  # pylint: disable=invalid-name
        email = database.Column(database.String(255), unique=True)
        password = database.Column(database.String(255))
        active = database.Column(database.Boolean())
        confirmed_at = database.Column(database.DateTime())
        roles = database.relationship('Role', secondary=roles_users, backref=database.backref('users', lazy='dynamic'))

    return UserRoleDatabase(database, User, Role)


def _add_configuration_to_app(app, config):
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECURITY_PASSWORD_SALT'] = b'Salt'
    app.config['SQLALCHEMY_DATABASE_URI'] = config.get('Runtime', 'user_database', fallback='sqlite:///')
    app.config['SECURITY_UNAUTHORIZED_VIEW'] = '/login'
    app.config['LOGIN_DISABLED'] = config.getboolean('Runtime', 'testing')
