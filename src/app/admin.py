# -*- coding: utf-8 -*-

from flask import render_template, request, flash

from app.security.decorator import roles_accepted
from database.mett_store import StorageException

# pylint: disable=redefined-outer-name


class AdminRoutes:
    def __init__(self, app, config, mett_store):
        self._app = app
        self._config = config
        self._mett_store = mett_store

        self._app.add_url_rule('/admin', 'admin', self._show_admin_home, methods=['GET', 'POST'])

        self._app.add_url_rule('/admin/create_order', 'admin/create_order', self._create_order, methods=['GET'])
        self._app.add_url_rule('/admin/cancel_order', 'admin/cancel_order', self._cancel_order, methods=['GET'])
        self._app.add_url_rule('/admin/close_order', 'admin/close_order', self._close_order, methods=['GET'])

        self._app.add_url_rule('/admin/balance', 'admin/balance', self._change_user_balance, methods=['GET', 'POST'])
        self._app.add_url_rule('/admin/formula', 'admin/formula', self._change_mett_formula, methods=['GET', 'POST'])
        self._app.add_url_rule('/admin/spare', 'admin/spare', self._assign_spare, methods=['GET', 'POST'])

        self._app.add_url_rule('/admin/purchase', 'admin/purchase', self._list_purchases, methods=['GET'])
        self._app.add_url_rule('/admin/purchase/authorize/<purchase_id>', 'admin/purchase/authorize/<purchase_id>', self._authorize_purchase, methods=['GET'])
        self._app.add_url_rule('/admin/purchase/decline/<purchase_id>', 'admin/purchase/decline/<purchase_id>', self._decline_purchase, methods=['GET'])

    @roles_accepted('admin')
    def _show_admin_home(self):
        if request.method == 'POST':
            expiry_date = request.form['expiry']
            try:
                self._mett_store.create_order_alt(expiry_date)
            except (StorageException, ValueError) as error:
                flash(str(error), 'warning')

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
        self._mett_store.process_order()
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

    @roles_accepted('admin')
    def _change_mett_formula(self):
        if request.method == 'POST':
            try:
                self._apply_change_to_formula(request)
            except RuntimeError:
                flash('Empty request. Please specify change of formula.', 'warning')

        return render_template('admin/formula.html', bun_classes=self._mett_store.list_bun_classes())

    @roles_accepted('admin')
    def _assign_spare(self):
        if request.method == 'POST':
            self._mett_store.assign_spare(bun_class=request.form['bun'], user=request.form['username'])
            return render_template('admin.html', order_exists=self._mett_store.active_order_exists())
        return render_template('admin/spare.html', bun_classes=self._mett_store.list_bun_classes(), users=[name for _id, name in self._mett_store.list_accounts()])

    def _apply_change_to_formula(self, request):
        if 'price' in request.form:
            self._mett_store.change_bun_price(request.form['bun'], request.form['price'])
        elif 'amount' in request.form:
            self._mett_store.change_mett_formula(request.form['bun'], request.form['amount'])
        else:
            raise RuntimeError('No change applied')


def _get_change_of_balance(request):
    return {
        'user': request.form['username'],
        'amount': request.form['amount']
    }
