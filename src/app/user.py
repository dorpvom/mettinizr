# -*- coding: utf-8 -*-
from contextlib import contextmanager

from flask import render_template, request, flash
from sqlalchemy.exc import SQLAlchemyError

from app.security.decorator import roles_accepted
from database.mett_store import StorageException
from database.user_store import UserRoleDatabase, password_is_legal

# pylint: disable=redefined-outer-name


class UserRoutes:
    def __init__(self, app, config, mett_store, user_database, user_interface: UserRoleDatabase):
        self._app = app
        self._config = config
        self._mett_store = mett_store
        self._user_interface = user_interface
        self._user_database = user_database

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

        try:
            users = list(self._generate_user_information())
        except StorageException as error:
            flash(str(error), 'danger')
            users = list()

        return render_template('user.html', users=users, existing_roles=[role.name for role in self._user_interface.list_roles()])

    @roles_accepted('admin')
    def _delete_user(self, name):
        try:
            self._mett_store.delete_account(name)
            with user_db_session(self._user_database):
                self._user_interface.delete_user(user=self._user_interface.find_user(email=name))
        except StorageException as error:
            flash(str(error), 'warning')
        except RuntimeError:
            flash('Failed to delete user account', 'warning')
        return self._show_user_home()

    def _generate_user_information(self):
        for user in self._user_interface.list_users():
            information = {
                'name': user.email,
                'active': user.is_active,
                'roles': self._extract_roles(user.roles),
                'balance': self._mett_store.get_account_information(user.email)['balance']
            }
            yield information

    @staticmethod
    def _extract_roles(roles):
        return ', '.join((role.name for role in roles))

    def _handle_create_user(self):
        try:
            if not password_is_legal(request.form['new_password']):
                raise ValueError('Please choose legal password')

            with user_db_session(self._user_database):
                self._user_interface.create_user(email=request.form['new_user'], password=request.form['new_password'])
                self._user_interface.add_role_to_user(user=self._user_interface.find_user(email=request.form['new_user']), role=self._config.get('User', 'default_role'))

            self._mett_store.create_account(request.form['new_user'])

        except (StorageException, ValueError) as error:
            flash(str(error), 'warning')
        except RuntimeError:
            flash('Can\'t create user {}. Might already exist. Otherwise check for bad spelling.'.format(request.form['new_user']), 'warning')

    def _handle_added_role(self):
        with user_db_session(self._user_database):
            self._user_interface.add_role_to_user(user=self._user_interface.find_user(email=request.form['add_role_username']), role=request.form['added_role'])

    def _handle_removed_role(self):
        with user_db_session(self._user_database):
            self._user_interface.remove_role_from_user(user=self._user_interface.find_user(email=request.form['remove_role_username']), role=request.form['removed_role'])


@contextmanager
def user_db_session(database):
    session = database.session
    try:
        yield session
        session.commit()
    except (SQLAlchemyError, TypeError) as exception:
        session.rollback()
        raise RuntimeError('Error while accessing user database: {}'.format(exception))
