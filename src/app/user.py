# -*- coding: utf-8 -*-
from contextlib import contextmanager

from flask import render_template, request, flash, redirect, url_for
from flask_security import current_user
from sqlalchemy.exc import SQLAlchemyError

from app.security.decorator import roles_accepted
from database.mett_store import StorageException
from database.user_store import UserRoleDatabase, password_is_legal

# pylint: disable=redefined-outer-name


class UserRoutes:
    def __init__(self, app, config, mett_store, user_interface: UserRoleDatabase):
        self._app = app
        self._config = config
        self._mett_store = mett_store
        self._user_interface = user_interface

        self._app.add_url_rule('/user', 'user', self._show_user_home, methods=['GET', 'POST'])
        self._app.add_url_rule('/user/delete/<name>', 'user/delete/<name>', self._delete_user, methods=['GET'])

    @roles_accepted('admin')
    def _show_user_home(self):
        if request.method == 'POST':
            if 'new_user' in request.form:
                self._handle_create_user()
            elif 'add_role_username' in request.form:
                self._handle_added_role()
            elif 'remove_role_username' in request.form:
                self._handle_removed_role()
            elif 'new_password_confirm' in request.form:
                self._handle_password_change()
            else:
                flash('Unknown action was requested')

        try:
            users = list(self._generate_user_information())
        except StorageException as error:
            flash(str(error), 'danger')
            users = list()

        return render_template('user.html', users=users, existing_roles=[role['name'] for role in self._user_interface.list_roles()])

    @roles_accepted('admin')
    def _delete_user(self, name):
        try:
            admin = current_user.name if not current_user.is_anonymous else 'anonymous'
            balance = self._mett_store.get_account_information(name)['balance']
            self._mett_store.change_balance(name, -balance, admin)
            self._mett_store.delete_account(name)
            self._user_interface.delete_user(name)
        except StorageException as error:
            flash(str(error), 'warning')
        except RuntimeError:
            flash('Failed to delete user account', 'warning')
        return redirect(url_for('user'))

    def _generate_user_information(self):
        for user in self._user_interface.list_users():
            information = {
                'name': user['name'],
                'roles': user['roles'],
                'balance': self._mett_store.get_account_information(user['name'])['balance']
            }
            yield information

    @staticmethod
    def _extract_roles(roles):
        return ', '.join((role.name for role in roles))

    def _handle_create_user(self):
        try:
            if not password_is_legal(request.form['new_password']):
                raise ValueError('Please choose legal password')

            self._user_interface.create_user(name=request.form['new_user'], password=request.form['new_password'])
            self._user_interface.add_role_to_user(user=request.form['new_user'], role=self._config.get('User', 'default_role'))

            self._mett_store.create_account(request.form['new_user'])

        except (StorageException, ValueError) as error:
            flash(str(error), 'warning')
        except RuntimeError:
            flash('Can\'t create user {}. Might already exist. Otherwise check for bad spelling.'.format(request.form['new_user']), 'warning')

    def _handle_added_role(self):
        self._user_interface.add_role_to_user(user=request.form['add_role_username'], role=request.form['added_role'])

    def _handle_removed_role(self):
        self._user_interface.remove_role_from_user(user=request.form['remove_role_username'], role=request.form['removed_role'])

    def _handle_password_change(self):
        new_password = request.form['new_password']
        new_password_confirm = request.form['new_password_confirm']

        if new_password != new_password_confirm:
            flash('Error: new password did not match', 'warning')
        elif not password_is_legal(new_password):
            flash('Error: password is not legal. Please choose another password.')
        else:
            self._user_interface.change_password(request.form['name'], new_password)
            flash('password change successful', 'success')


@contextmanager
def user_db_session(database):
    session = database.session
    try:
        yield session
        session.commit()
    except (SQLAlchemyError, TypeError) as exception:
        session.rollback()
        raise RuntimeError('Error while accessing user database: {}'.format(exception))
