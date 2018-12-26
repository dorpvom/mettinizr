# -*- coding: utf-8 -*-

from flask import render_template, request

from app.security.decorator import roles_accepted
from database.mett_store import MettStore


class AdminRoutes:
    def __init__(self, app, config, api=None):
        self._app = app
        self._config = config
        self._api = api
        self._mett_store = MettStore(config=self._config)

        self._app.add_url_rule('/admin', 'admin', self._show_admin_home, methods=['GET'])

        self._app.add_url_rule('/admin/create_order', 'admin/create_order', self._create_order, methods=['GET'])
        self._app.add_url_rule('/admin/cancel_order', 'admin/cancel_order', self._cancel_order, methods=['GET'])
        self._app.add_url_rule('/admin/close_order', 'admin/close_order', self._close_order, methods=['GET'])

        self._app.add_url_rule('/admin/balance', 'admin/balance', self._change_user_balance, methods=['GET', 'POST'])

        self._app.add_url_rule('/admin/purchase', 'admin/purchase', self._list_purchases, methods=['GET'])
        self._app.add_url_rule('/admin/purchase/authorize/<purchase_id>', 'admin/purchase/authorize/<purchase_id>', self._authorize_purchase, methods=['GET'])
        self._app.add_url_rule('/admin/purchase/decline/<purchase_id>', 'admin/purchase/decline/<purchase_id>', self._decline_purchase, methods=['GET'])

    @roles_accepted('admin')
    def _show_admin_home(self):
        return render_template('admin.html', order_exists=self._mett_store.active_order_exists())

    @roles_accepted('admin')
    def _create_order(self):
        self._mett_store.create_order()
        return self._show_admin_home()

    @roles_accepted('admin')
    def _cancel_order(self):
        self._mett_store.drop_order()
        return self._show_admin_home()

    @roles_accepted('admin')
    def _close_order(self):
        self._mett_store.expire_order()
        return self._show_admin_home()

    @roles_accepted('admin')
    def _change_user_balance(self):
        if request.method == 'POST':
            transaction = _get_change_of_balance(request)
            self._mett_store.book_money(transaction['user'], float(transaction['amount']))
            return self._show_admin_home()

        user_names = [name for _id, name in self._mett_store.list_accounts()]
        return render_template('admin/balance.html', users=user_names)

    @roles_accepted('admin')
    def _list_purchases(self):
        purchases = self._mett_store.list_purchases()
        return render_template('admin/purchase.html', purchases=purchases)

    @roles_accepted('admin')
    def _authorize_purchase(self, purchase_id):
        self._mett_store.authorize_purchase(purchase_id)
        return self._list_purchases()

    @roles_accepted('admin')
    def _decline_purchase(self, purchase_id):
        self._mett_store.decline_purchase(purchase_id)
        return self._list_purchases()


def _get_change_of_balance(request):
    return {
        'user': request.form['username'],
        'amount': request.form['amount']
    }
