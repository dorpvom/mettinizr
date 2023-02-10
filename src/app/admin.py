# -*- coding: utf-8 -*-
from typing import Dict, Union

from flask import render_template, request, flash
from flask_security import current_user
from app.security.decorator import roles_accepted
from database.interface import MettInterface, DatabaseError


# pylint: disable=redefined-outer-name


class AdminRoutes:
    def __init__(self, app, config, mett_store: MettInterface):
        self._app = app
        self._config = config
        self._mett_store = mett_store

        self._app.add_url_rule('/admin', 'admin', self._show_admin_home, methods=['GET', 'POST'])

        self._app.add_url_rule('/admin/cancel_order', 'admin/cancel_order', self._cancel_order, methods=['GET'])
        self._app.add_url_rule('/admin/close_order', 'admin/close_order', self._close_order, methods=['GET'])

        self._app.add_url_rule('/admin/balance', 'admin/balance', self._change_user_balance, methods=['GET', 'POST'])
        self._app.add_url_rule('/admin/formula', 'admin/formula', self._change_mett_formula, methods=['GET', 'POST'])
        self._app.add_url_rule('/admin/spare', 'admin/spare', self._assign_spare, methods=['GET', 'POST'])

        self._app.add_url_rule('/admin/purchase', 'admin/purchase', self._list_purchases, methods=['GET'])
        self._app.add_url_rule('/admin/purchase/authorize/<purchase_id>', 'admin/purchase/authorize/<purchase_id>', self._authorize_purchase, methods=['GET'])
        self._app.add_url_rule('/admin/purchase/decline/<purchase_id>', 'admin/purchase/decline/<purchase_id>', self._decline_purchase, methods=['GET'])

        self._app.add_url_rule('/admin/deposit', 'admin/deposit', self._list_deposits, methods=['GET'])
        self._app.add_url_rule('/admin/assign', 'admin/assign', self._assign_bun, methods=['GET', 'POST'])
        self._app.add_url_rule('/admin/reroute', 'admin/reroute', self._reroute_bun, methods=['GET', 'POST'])

    @roles_accepted('admin')
    def _show_admin_home(self):
        if request.method == 'POST':
            expiry_date = request.form['expiry']
            try:
                self._mett_store.create_order(expiry_date)
            except (DatabaseError, ValueError) as error:
                flash(str(error), 'warning')

        return render_template('admin.html', order_exists=self._mett_store.active_order_exists(), store_stats=get_store_stats(self._mett_store))

    @roles_accepted('admin')
    def _cancel_order(self):
        self._mett_store.drop_current_order()
        return self._show_admin_home()

    @roles_accepted('admin')
    def _close_order(self):
        self._mett_store.process_order()
        return self._show_admin_home()

    @roles_accepted('admin')
    def _change_user_balance(self):
        if request.method == 'POST':
            transaction = _get_change_of_balance(request)
            admin = current_user.name if not current_user.is_anonymous else 'anonymous'
            self._mett_store.change_balance(account=transaction['user'], amount=transaction['amount'], admin=admin)

            return render_template('admin.html', order_exists=self._mett_store.active_order_exists(), store_stats=get_store_stats(self._mett_store))

        user_names = self._mett_store.list_accounts()
        return render_template('admin/balance.html', users=user_names)

    @roles_accepted('admin')
    def _list_purchases(self):
        purchases = self._mett_store.list_purchases(processed=True)

        processed = [purchase for purchase in purchases if purchase.processed['by'] is not None]
        unprocessed = [purchase for purchase in purchases if not purchase.processed['by']]

        return render_template('admin/purchase.html', processed=processed, unprocessed=unprocessed)

    @roles_accepted('admin')
    def _authorize_purchase(self, purchase_id):
        admin = current_user.name if not current_user.is_anonymous else 'anonymous'
        self._mett_store.authorize_purchase(purchase_id, admin)
        return self._list_purchases()

    @roles_accepted('admin')
    def _decline_purchase(self, purchase_id):
        admin = current_user.name if not current_user.is_anonymous else 'anonymous'
        self._mett_store.decline_purchase(purchase_id, admin)
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
            return render_template('admin.html', order_exists=self._mett_store.active_order_exists(), store_stats=get_store_stats(self._mett_store))
        return render_template('admin/spare.html', bun_classes=self._mett_store.list_bun_classes(), users=self._mett_store.list_accounts())

    def _apply_change_to_formula(self, request):
        if 'price' in request.form:
            self._mett_store.change_bun_price(request.form['bun'], request.form['price'])
        elif 'amount' in request.form:
            self._mett_store.change_mett_formula(request.form['bun'], request.form['amount'])
        else:
            raise RuntimeError('No change applied')

    @roles_accepted('admin')
    def _list_deposits(self):
        deposits = self._mett_store.get_deposits()
        return render_template('admin/deposit.html', deposits=deposits)

    @roles_accepted('admin')
    def _assign_bun(self):
        if request.method == 'POST':
            self._mett_store.order_bun(request.form['username'], request.form['bun'])
            return render_template('admin.html', order_exists=self._mett_store.active_order_exists(), store_stats=get_store_stats(self._mett_store))
        return render_template('admin/assign.html', bun_classes=self._mett_store.list_bun_classes(), users=self._mett_store.list_accounts(), order_exists=self._mett_store.active_order_exists())

    @roles_accepted('admin')
    def _reroute_bun(self):
        if request.method == 'POST':
            try:
                self._mett_store.reroute_bun(bun_class=request.form['bun'], user=request.form['username'], target=request.form['target'])
            except ValueError:
                flash('User {} has not order a {} bun'.format(request.form['username'], request.form['bun']))
            return render_template('admin.html', order_exists=self._mett_store.active_order_exists(), store_stats=get_store_stats(self._mett_store))
        return render_template('admin/reroute.html', bun_classes=self._mett_store.list_bun_classes(), users=self._mett_store.list_accounts(), order_exist=self._mett_store.active_order_exists())


def _get_change_of_balance(request):
    return {
        'user': request.form['username'],
        'amount': float(request.form['added']) if 'added' in request.form else 0.0 - float(request.form['removed'])
    }


def get_store_stats(mett_store: MettInterface) -> Dict[str, Union[int, float]]:
    deposits = sum(deposit['amount'] for deposit in mett_store.get_deposits())
    purchases = sum(purchase['price'] for purchase in mett_store.list_purchases(processed=True))
    return {
        'sum_of_deposits': deposits,
        'sum_of_purchases': purchases,
        'balance': deposits - purchases,
        'sum_of_buns': sum(len(order['orders']) for order in mett_store.get_all_order_information()),
    }
