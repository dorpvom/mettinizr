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
        users = [[user.email, user.is_active, user.roles] for user in self._user_store.list_users()]
        return render_template('user.html', users=users)
