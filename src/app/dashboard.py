# -*- coding: utf-8 -*-

from flask import render_template
from flask_security import current_user, login_required

from app.security.decorator import roles_accepted
from database.mett_store import StorageException


class DashboardRoutes:
    def __init__(self, app, config, mett_store):
        self._app = app
        self._config = config
        self._mett_store = mett_store

        self._app.add_url_rule('/', '', self._show_home_dashboard)

    @login_required
    @roles_accepted('user', 'admin')
    def _show_home_dashboard(self):
        user = current_user.name
        information = self._mett_store.get_account_information(user)
        order_exists, order = True, {}
        try:
            order = self._mett_store.get_current_user_buns(user)
        except StorageException:
            order_exists = False

        order_history, mean_buns = self._mett_store.get_order_history(user)
        return render_template('dashboard.html', order_exists=order_exists, username=user, order=order, balance=information['balance'], history=order_history, mean_buns=mean_buns)
