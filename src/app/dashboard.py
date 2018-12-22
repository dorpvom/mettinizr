# -*- coding: utf-8 -*-

from flask import render_template
from flask_security import current_user, login_required

from app.security.decorator import roles_accepted
from database.mett_store import MettStore, StorageException


class DashboardRoutes:
    def __init__(self, app, config, api=None):
        self._app = app
        self._config = config
        self._api = api
        self._mett_store = MettStore(config=self._config)

        self._app.add_url_rule('/', '', self._show_home_dashboard)

    @login_required
    @roles_accepted('user', 'admin')
    def _show_home_dashboard(self):
        user = current_user.email
        information = self._mett_store.get_account_information(user)
        order_exists, order = True, {}
        try:
            order = self._mett_store.get_current_user_buns(user)
        except StorageException:
            order_exists = False

        return render_template('dashboard.html', order_exists=order_exists, username=user, order=order, balance=information['balance'])
