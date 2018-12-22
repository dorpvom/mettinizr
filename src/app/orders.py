# -*- coding: utf-8 -*-

from flask import render_template, request
from flask_security import current_user

from app.security.decorator import roles_accepted
from database.mett_store import MettStore


class OrderRoutes:
    def __init__(self, app, config, api=None):
        self._app = app
        self._config = config
        self._api = api
        self._mett_store = MettStore(config=self._config)

        self._app.add_url_rule('/order', 'order', self._show_order_home, methods=['GET', 'POST'])

    @roles_accepted('user', 'admin')
    def _show_current_order(self):
        return render_template('order/current.html', orders=[1,2,3,4])

    @roles_accepted('user', 'admin')
    def _show_order_home(self):
        if request.method == 'POST':
            mett_order = _get_order_from_request(request)
            user = current_user.email
            for _ in range(int(mett_order['amount'])):
                self._mett_store.order_bun(user, mett_order['bun_class'])

        return render_template('order.html', bun_classes=self._mett_store.list_bun_classes())


def _get_order_from_request(request):
    return {
        'bun_class': request.form['orderClass'],
        'amount': request.form['orderAmount']
    }
