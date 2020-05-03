'''
account: id, name, balance (name primary key)
order: id, processed, expiry_date, orders (orders list of (account, bun), with account foreign_key on account.id and bun foreign_key on price.id)
buns: id, bun_class, price, mett
purchase: id, account, price, purpose, processed (account foreign_key on accound.name)
deposits: id, admin, user, amount (admin fk account.name, user fk account.name)
'''

import datetime
from time import time

from bson.objectid import ObjectId
from pymongo import MongoClient


class StorageException(Exception):
    pass


class MettStore:

    def __init__(self, config, ):
        self._config = config

        self._client = MongoClient('mongodb://{}:{}'.format(self._config.get('Database', 'mongo_server'), self._config.get('Database', 'mongo_port')), connect=False)
        self._mett_base = self._client[self._config.get('Database', 'main_database')]

        self._account = self._mett_base.account
        self._order = self._mett_base.order
        self._buns = self._mett_base.price
        self._purchase = self._mett_base.purchase
        self._deposit = self._mett_base.deposit

        self._init_tables()

    def _init_tables(self):
        if self._buns.count_documents({}) == 0:
            for bun in self._config.get('Mett', 'default_buns').split(','):
                self._buns.insert_one({'bun_class': bun.strip(), 'price': self._config.getfloat('Mett', 'default_price'), 'mett': self._config.getfloat('Mett', 'default_grams')})

    # -------------- admin functions --------------

    def create_account(self, name):
        if self.account_exists(name):
            raise StorageException('Account {} exists'.format(name))
        return self._account.insert_one({'name': name, 'balance': 0.0}).inserted_id

    def delete_account(self, name):
        if not self.account_exists(name):
            raise StorageException('Account {} does not exist'.format(name))
        return self._account.delete_one({'name': name}).deleted_count

    def change_balance(self, account, amount, admin):
        self._book_money(account, amount)
        self._deposit.insert_one({'admin': admin, 'user': account, 'amount': amount, 'timestamp': time()})

    def _book_money(self, account, amount):
        # Increase balance of account by amount and register deposit by admin
        self._account.update_one({'name': account}, {'$inc': {'balance': amount}})

    def get_deposits(self):
        deposits = self._deposit.find()
        return [
            {
                'amount': deposit['amount'],
                'user': deposit['user'],
                'admin': deposit['admin'],
                'timestamp': deposit['timestamp']
            } for deposit in deposits
        ]

    def list_accounts(self):
        # return list of (accound.id, account.name) tuples
        return [(entry['_id'], entry['name']) for entry in self._account.find()]

    def process_order(self):
        # set expire of current order to true and decrease balances according to order
        current_order = self._get_current_order()
        for account, bun in current_order['orders']:
            self._charge_bun(account, bun)
        self._order.update_one({'processed': False}, {'$set': {'processed': True}})

    def drop_current_order(self):
        # drop current order
        self._order.delete_one({'processed': False})

    def list_purchases(self, processed=False):
        # list purchases, if processed is false only those that have not been authorized or declined
        query = {} if processed else {'processed.authorized': False}
        purchases = list(self._purchase.find(query, {'account': 1, 'price': 1, '_id': 1, 'purpose': 1}))
        for purchase in purchases:
            purchase['_id'] = str(purchase['_id'])
        return purchases

    def authorize_purchase(self, purchase_id, admin):
        # add purchase.amount to purchase.account.balance
        purchase = self._purchase.find_one({'_id': ObjectId(purchase_id)})
        self._book_money(purchase['account'], float(purchase['price']))
        self._purchase.update_one({'_id': ObjectId(purchase_id)}, {'$set': {'processed': {'authorized': True, 'at': time(), 'by': admin}}})

    def decline_purchase(self, purchase_id, admin):
        # drop purchase
        self._purchase.update_one({'_id': ObjectId(purchase_id)}, {'$set': {'processed': {'authorized': True, 'at': time(), 'by': admin}}})

    def change_mett_formula(self, bun, amount):
        # set mett_formula.amount for referenced bun
        if self._buns.count_documents({'bun_class': bun}) < 1:
            raise StorageException('Bun does not exist')
        self._buns.update_one({'bun_class': bun}, {'$set': {'mett': float(amount)}})

    def change_bun_price(self, bun, price):
        # set mett_formula.amount for referenced bun
        if self._buns.count_documents({'bun_class': bun}) < 1:
            raise StorageException('Bun does not exist')
        self._buns.update_one({'bun_class': bun}, {'$set': {'price': float(price)}})

    def assign_spare(self, bun_class, user):
        self._charge_bun(user, bun_class)

    # -------------- user functions --------------

    def active_order_exists(self):
        return self._order.count_documents({'processed': False}) > 0

    def account_exists(self, name):
        return self._account.count_documents({'name': name}) > 0

    def get_account_information(self, account):
        # get (id, name, balance) for account
        if not self.account_exists(account):
            raise StorageException('No existing account {}'.format(account))
        account_information = self._account.find_one({'name': account})
        account_information['_id'] = str(account_information['_id'])
        return account_information

    def order_bun(self, account, bun_class):  # throws Exception if no current order
        # add (account, bun_class) to current order
        current_order = self._get_current_order()
        if self.current_order_is_expired():
            raise StorageException('Order has expired. You are not allowed to order anymore.')
        orders = current_order['orders']
        orders.append((account, bun_class))
        self._order.update_one({'_id': current_order['_id']}, {'$set': {'orders': orders}})

    def reroute_bun(self, bun_class, user, target):
        user_buns = self.get_current_user_buns(user)
        if user_buns[bun_class] == 0:
            raise ValueError('No {} bun order by {}'.format(bun_class, user))
        current_order = self._get_current_order()
        new_orders = self._reroute_from_user_to_target(bun_class, current_order, target, user)
        self._order.update_one({'_id': current_order['_id']}, {'$set': {'orders': new_orders}})

    @staticmethod
    def _reroute_from_user_to_target(bun_class, current_order, target, user):
        new_orders, rerouted = [], False
        for account, ordered_bun in current_order['orders']:
            if account == user and ordered_bun == bun_class and not rerouted:
                new_orders.append((target, ordered_bun))
                rerouted = True
            else:
                new_orders.append((account, ordered_bun))
        if not rerouted:
            raise ValueError('Unknown problem in rerouting order')
        return new_orders

    def state_purchase(self, account, amount, purpose):
        # add account, amount, purpose as non processed purchase
        result = self._purchase.insert_one({'account': account, 'price': amount, 'purpose': purpose, 'timestamp': time(), 'processed': {'authorized': False, 'at': None, 'by': None}})
        return result.inserted_id

    def get_order_history(self, user):
        # TODO Please refactor
        # get list of (order_id, orders) where orders is slice of orders ordered by account
        orders = list(self._order.find({'processed': True}))
        user_has_ordered, flag = 0, False
        order = {bun_class: 0 for bun_class in self.list_bun_classes()}
        for former_order in orders:
            for account, bun_class in former_order['orders']:
                if account == user:
                    order[bun_class] += 1
                    flag = True
            if flag:
                user_has_ordered += 1
                flag = False
        if user_has_ordered > 0:
            for bun_class in order:
                order[bun_class] = order[bun_class] / user_has_ordered
        mean_over_all = sum(order[bun] for bun in order)
        return order, mean_over_all

    def get_current_user_buns(self, user):
        # get list of buns ordered by user
        return self._get_order(lambda x: x == user)

    def get_current_bun_order(self):
        # get aggregated current bun order
        bun_order = self._get_order(lambda _: True)
        for spare in self._calculate_spares():
            bun_order[spare] += 1
        return bun_order

    def _get_order(self, filter_function):
        # get list of buns ordered by user
        current_order = self._get_current_order()
        order = {bun_class: 0 for bun_class in self.list_bun_classes()}

        for account, bun_class in current_order['orders']:
            if filter_function(account):
                order[bun_class] += 1

        return order

    def get_current_mett_order(self):
        # generate mett order from bun order
        bun_order = self.get_current_bun_order()
        return sum(self._get_mett(bun_class) * bun_order[bun_class] for bun_class in bun_order)

    def list_bun_classes(self) -> list:
        return [bun['bun_class'] for bun in self._buns.find({}, {'bun_class': 1})]

    def list_bun_classes_with_price(self) -> dict:
        return {bun['bun_class']: bun['price'] for bun in self._buns.find({}, {'bun_class': 1, 'price': 1})}

    def get_all_order_information(self):
        return list(self._order.find())

    # -------------- internal functions --------------

    def _calculate_spares(self):
        current_bun_order = self._get_order(lambda _: True)
        if 'Roeggelchen' in current_bun_order and (current_bun_order['Roeggelchen'] % 2) == 1:
            return ['Roeggelchen', 'Weizen']
        return ['Weizen', 'Roggen']

    def _get_mett(self, bun):
        return float(self._buns.find_one({'bun_class': bun}, {'mett': 1})['mett'])

    def _get_current_order(self):
        current_order = self._order.find_one({'processed': False})
        if not current_order:
            raise StorageException('No current order')
        return current_order

    def _charge_bun(self, account, bun):
        bun_price = self._buns.find_one({'bun_class': bun})['price']
        self._account.update_one({'name': account}, {'$inc': {'balance': 0 - float(bun_price)}})

    # -------------- internal functions --------------

    def create_order(self, expiry_date):
        if self._is_expired(expiry_date):
            raise StorageException('Please enter date that hasn\'t expired yet')
        if self.active_order_exists():
            raise StorageException('No new order can be initialized while another one is active')
        return self._order.insert_one({'expiry_date': expiry_date, 'processed': False, 'orders': []}).inserted_id

    def current_order_is_expired(self):
        if not self.active_order_exists():
            raise StorageException('There is no active order')
        return self._is_expired(self._get_current_order()['expiry_date'])

    def _is_expired(self, expiry_date):
        expiry_time = self._config.get('DEFAULT', 'expiry_time').strip()
        return datetime.datetime.strptime('{} {}'.format(expiry_date, expiry_time), '%Y-%m-%d %H:%M:%S') < datetime.datetime.now()
