from flask import render_template, request, flash
from flask_security import current_user

from app.security.decorator import roles_accepted
from database.interface import password_is_legal


# pylint: disable=redefined-outer-name


class ProfileRoutes:
    def __init__(self, app, config, database):
        self._app = app
        self._config = config
        self._database = database

        self._app.add_url_rule('/profile', 'profile', self._show_profile, methods=['GET', 'POST'])

    @roles_accepted('user', 'admin')
    def _show_profile(self):
        if request.method == 'POST':
            self._change_own_password()

        return render_template('profile/profile.html', user=current_user.name, roles=[role.name for role in current_user.roles])

    def _change_own_password(self):
        new_password = request.form['new_password']
        new_password_confirm = request.form['new_password_confirm']
        old_password = request.form['old_password']
        if new_password != new_password_confirm:
            flash('Error: new password did not match', 'warning')
        elif not self._database.password_is_correct(current_user.name, old_password):
            flash('Error: wrong password', 'warning')
        elif not password_is_legal(new_password):
            flash('Error: password is not legal. Please choose another password.')
        else:
            self._database.change_password(current_user.name, new_password)
            flash('password change successful', 'success')
