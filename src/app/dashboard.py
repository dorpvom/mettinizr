# -*- coding: utf-8 -*-

from flask import render_template
from flask_security import current_user
from app.security.decorator import roles_accepted
from database.mett_store import MettStore

class DashboardRoutes:
    def __init__(self, app, config, api=None):
        self._app = app
        self._config = config
        self._api = api
        self._mett_store = MettStore(config=self._config)

        self._app.add_url_rule('/', '', self._show_home_dashboard)

    @roles_accepted('user', 'admin')
    def _show_home_dashboard(self):
        name = current_user.email
        order = self._mett_store.get_current_user_buns(name)
        return render_template('dashboard.html', username=name, order=order)
