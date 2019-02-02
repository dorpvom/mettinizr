# -*- coding: utf-8 -*-

from flask import render_template

from app.security.decorator import roles_accepted
from database.user_store import UserRoleDatabase


# pylint: disable=redefined-outer-name


class UserRoutes:
    def __init__(self, app, config, mett_store, user_store: UserRoleDatabase):
        self._app = app
        self._config = config
        self._mett_store = mett_store
        self._user_store = user_store

        self._app.add_url_rule('/user', 'user', self._show_user_home, methods=['GET'])

    @roles_accepted('admin')
    def _show_user_home(self):
        users = list(self._generate_user_information())
        return render_template('user.html', users=users)

    def _generate_user_information(self):
        for user in self._user_store.list_users():
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
