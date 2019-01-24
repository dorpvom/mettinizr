from contextlib import contextmanager

from flask import render_template, request, flash
from flask_security import current_user
from passlib.context import CryptContext
from sqlalchemy.exc import SQLAlchemyError

from app.security.decorator import roles_accepted

# pylint: disable=redefined-outer-name


class ProfileRoutes:
    def __init__(self, app, config, user_database, database_interface):
        self._app = app
        self._config = config
        self._user_database = user_database
        self._database_interface = database_interface

        self._app.add_url_rule('/profile', 'profile', self._show_profile, methods=['GET', 'POST'])

    @contextmanager
    def user_db_session(self):
        session = self._user_database.session
        try:
            yield session
            session.commit()
        except (SQLAlchemyError, TypeError) as exception:
            session.rollback()
            raise RuntimeError('Error while accessing user database: {}'.format(exception))

    @roles_accepted('user', 'admin')
    def _show_profile(self):
        if request.method == 'POST':
            self._change_own_password()

        return render_template('profile/profile.html', user=current_user)

    def _change_own_password(self):
        new_password = request.form['new_password']
        new_password_confirm = request.form['new_password_confirm']
        old_password = request.form['old_password']
        if new_password != new_password_confirm:
            flash('Error: new password did not match', 'warning')
        elif not self._database_interface.password_is_correct(current_user.email, old_password):
            flash('Error: wrong password', 'warning')
        elif not self._password_is_legal(new_password):
            flash('Error: password is not legal. Please choose another password.')
        else:
            with self.user_db_session():
                self._database_interface.change_password(current_user.email, new_password)
                flash('password change successful', 'success')

    @staticmethod
    def _password_is_legal(password):
        if not password:
            return False
        schemes = ['bcrypt', 'des_crypt', 'pbkdf2_sha256', 'pbkdf2_sha512', 'sha256_crypt', 'sha512_crypt', 'plaintext']
        ctx = CryptContext(schemes=schemes)
        return ctx.identify(password) == 'plaintext'
