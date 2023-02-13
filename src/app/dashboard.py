# -*- coding: utf-8 -*-

from flask import render_template
from flask_security import current_user, login_required

from app.security.decorator import roles_accepted
from database.interface import DatabaseError


class DashboardRoutes:
    def __init__(self, app, config, database):
        self._app = app
        self._config = config
        self._database = database

        self._app.add_url_rule('/', '', self._show_home_dashboard)

    @login_required
    @roles_accepted('user', 'admin')
    def _show_home_dashboard(self):
        user = current_user.name
        balance = self._database.get_balance(user)
        order_exists, order = True, {}
        try:
            order = self._database.get_current_user_buns(user)
        except DatabaseError:
            order_exists = False

        order_history, mean_buns = self._database.get_order_history(user)
        return render_template('dashboard.html', order_exists=order_exists, username=user, order=order, balance=balance, history=order_history, mean_buns=mean_buns)
