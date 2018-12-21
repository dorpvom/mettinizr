# -*- coding: utf-8 -*-

from flask import render_template

from app.security.decorator import roles_accepted


class OrderRoutes:
    def __init__(self, app, config, api=None):
        self._app = app
        self._config = config
        self._api = api

        self._app.add_url_rule('/order/current', 'order/current', self._show_current_order)

    @roles_accepted('user', 'admin')
    def _show_current_order(self):
        return render_template('order/current.html', orders=[1,2,3,4])
