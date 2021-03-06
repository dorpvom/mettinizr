from flask import flash, render_template, request, url_for, redirect
from flask_security import current_user

from app.security.decorator import roles_accepted

# pylint: disable=redefined-outer-name


class OrderRoutes:
    def __init__(self, app, config, mett_store):
        self._app = app
        self._config = config
        self._mett_store = mett_store

        self._app.add_url_rule('/order', 'order', self._show_order_home, methods=['GET', 'POST'])
        self._app.add_url_rule('/order/purchase', 'order/purchase', self._state_purpose, methods=['GET', 'POST'])
        self._app.add_url_rule('/order/previous', 'order/previous', self._show_previous_orders, methods=['GET'])

    @roles_accepted('user', 'admin')
    def _show_order_home(self):
        if request.method == 'POST':
            mett_order = _get_order_from_request(request)

            try:
                for _ in range(int(mett_order['amount'])):
                    self._mett_store.order_bun(current_user.name, mett_order['bun_class'])
            except ValueError:
                flash('Please state amount of buns')

            return redirect(url_for(''))

        allowed_to_order, bun_classes, buns, mett, order_exists = self._prepare_data_for_order_page()
        return render_template('order.html', allowed_to_order=allowed_to_order, bun_classes=bun_classes, order_exists=order_exists, buns=buns, mett=mett)

    @roles_accepted('user', 'admin')
    def _state_purpose(self):
        if request.method == 'POST':
            transaction = _get_purchase_information(request)
            self._mett_store.state_purchase(current_user.name, float(transaction['amount']), transaction['purpose'])

            allowed_to_order, bun_classes, buns, mett, order_exists = self._prepare_data_for_order_page()
            return render_template('order.html', allowed_to_order=allowed_to_order, bun_classes=self._mett_store.list_bun_classes(), order_exists=order_exists, buns=buns, mett=mett)

        return render_template('order/purchase.html')

    @roles_accepted('user', 'admin')
    def _show_previous_orders(self):
        all_information = self._mett_store.get_all_order_information()

        for order in all_information:
            order['_id'] = str(order['_id'])
            order['orders'] = rearrange_ordered_buns(order['orders'])

        return render_template('order/previous.html', orders=all_information)

    def _prepare_data_for_order_page(self):
        order_exists = self._mett_store.active_order_exists()
        allowed_to_order = not self._mett_store.current_order_is_expired() if order_exists else False
        if order_exists:
            buns = self._mett_store.get_current_bun_order()
            mett = self._mett_store.get_current_mett_order()
        else:
            buns, mett = None, None
        bun_classes = self._mett_store.list_bun_classes_with_price()
        return allowed_to_order, bun_classes, buns, mett, order_exists


def rearrange_ordered_buns(orders):
    return {
        user: [bun for name, bun in orders if name == user]
        for user in {name for name, _ in orders}
    }


def _get_order_from_request(request):
    return {
        'bun_class': request.form['orderClass'],
        'amount': request.form['orderAmount']
    }


def _get_purchase_information(request):
    return {
        'purpose': request.form['purpose'],
        'amount': request.form['amount']
    }
