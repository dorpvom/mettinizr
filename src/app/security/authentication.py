from flask_security import Security, UserMixin, RoleMixin
from flask_sqlalchemy import SQLAlchemy

from database.user_store import UserRoleDatabase


def add_flask_security_to_app(app, config):
    _add_configuration_to_app(app, config)

    db = SQLAlchemy(app)

    user_interface = create_user_interface(db)
    _ = Security(app, user_interface)

    return db, user_interface


def create_user_interface(db):
    roles_users = db.Table('roles_users', db.Column('user_id', db.Integer(), db.ForeignKey('user.id')), db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

    class Role(db.Model, RoleMixin):
        id = db.Column(db.Integer(), primary_key=True)  # pylint: disable=invalid-name
        name = db.Column(db.String(80), unique=True)
        description = db.Column(db.String(255))

    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
        email = db.Column(db.String(255), unique=True)
        password = db.Column(db.String(255))
        active = db.Column(db.Boolean())
        confirmed_at = db.Column(db.DateTime())
        roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

    return UserRoleDatabase(db, User, Role)


def _add_configuration_to_app(app, config):
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECURITY_PASSWORD_SALT'] = b'Salt'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
    app.config['SECURITY_UNAUTHORIZED_VIEW'] = '/login'
    app.config['LOGIN_DISABLED'] = not config.getboolean('Runtime', 'testing')
