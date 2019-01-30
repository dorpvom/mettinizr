'''
account: id, name, balance (name private_key)
order: id, processed, expiry_date, orders (orders list of (account, bun), with account foreign_key on account.id and bun foreign_key on price.id)
buns: id, bun_class, price, mett
purchase: id, account, price, purpose, processed (account foreign_key on accound.name)
'''
import datetime

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
        self._alt_order = self._mett_base.alt_order
        self._buns = self._mett_base.price
        self._purchase = self._mett_base.purchase

        self._init_tables()

    def _init_tables(self):
        if self._buns.count_documents({}) == 0:
            for bun in self._config.get('Mett', 'default_buns').split(','):
                self._buns.insert_one({'bun_class': bun.strip(), 'price': self._config.getfloat('Mett', 'default_price'), 'mett': self._config.getfloat('Mett', 'default_grams')})

    # -------------- admin functions --------------

    def create_account(self, name):
        if self.account_exists(name):
            raise StorageException('Account {} exists'.format(name))
        result = self._account.insert_one({'name': name, 'balance': 0.0})
        return result.inserted_id

    def book_money(self, account, amount):
        # Increase balance of account by amount
        self._account.update_one({'name': account}, {'$inc': {'balance': amount}})

    def list_accounts(self):
        # return list of (accound.id, account.name) tuples
        return [(entry['_id'], entry['name']) for entry in self._account.find()]

    def process_order(self):
        # set expire of current order to true and decrease balances according to order
        current_order = self._get_current_order()
        for account, bun in current_order['orders']:
            self._charge_bun(account, bun)
        self._alt_order.update_one({'processed': False}, {'$set': {'processed': True}})

    def drop_order(self, order=None):
        # TODO split in two functions
        # drop order by id or current order
        if order:
            self._order.delete_one({'_id': ObjectId(order)})
        else:
            self._order.delete_one({'processed': False})

    def list_purchases(self, processed=False):
        # list purchases, if processed is false only those that have not been authorized or declined
        query = {} if processed else {'processed': False}
        purchases = list(self._purchase.find(query, {'account': 1, 'price': 1, '_id': 1, 'purpose': 1}))
        for purchase in purchases:
            purchase['_id'] = str(purchase['_id'])
        return purchases

    def authorize_purchase(self, purchase_id):
        # add purchase.amount to purchase.account.balance
        purchase = self._purchase.find_one({'_id': ObjectId(purchase_id)})
        self.book_money(purchase['account'], float(purchase['price']))
        self._purchase.update_one({'_id': ObjectId(purchase_id)}, {'$set': {'processed': True}})

    def decline_purchase(self, purchase_id):
        # drop purchase
        self._purchase.update_one({'_id': ObjectId(purchase_id)}, {'$set': {'processed': True}})

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

    def assign_spare(self, bun_class, user):  # TODO change to use of names not id
        self._charge_bun(self._get_account_id_from_name(user), self._resolve_bun(bun_class))

    # -------------- user functions --------------

    def active_order_exists(self):
        return self._alt_order.count_documents({'processed': False}) > 0

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
        orders.append((self._get_account_id_from_name(account), self._resolve_bun(bun_class)))
        self._order.update_one({'_id': current_order['_id']}, {'$set': {'orders': orders}})

    def state_purchase(self, account, amount, purpose):
        # add account, amount, purpose as non processed purchase
        result = self._purchase.insert_one({'account': account, 'price': amount, 'purpose': purpose, 'processed': False})
        return result.inserted_id

    def get_order_history(self, user):
        # TODO Please refactor
        # get list of (order_id, orders) where orders is slice of orders ordered by account
        orders = list(self._order.find({'processed': True}))
        user_has_ordered, flag = 0, False
        order = {bun_class: 0 for bun_class in self.list_bun_classes()}
        for former_order in orders:
            for account, bun in former_order['orders']:
                if account == self._get_account_id_from_name(user):
                    order[self._resolve_bun(bun)] += 1
                    flag = True
            if flag:
                user_has_ordered += 1
                flag = False
        if user_has_ordered > 0:
            for bun in order:
                order[bun] = order[bun] / user_has_ordered
        mean_over_all = sum(order[bun] for bun in order)
        return order, mean_over_all

    def get_current_user_buns(self, user):
        # get list of buns ordered by user
        return self._get_order(lambda x: x == self._get_account_id_from_name(user))

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

        for account, bun in current_order['orders']:
            if filter_function(account):
                order[self._resolve_bun(bun)] += 1

        return order

    def get_current_mett_order(self):
        # generate mett order from bun order
        bun_order = self.get_current_bun_order()
        return sum(self._get_mett(self._resolve_bun(bun_class)) * bun_order[bun_class] for bun_class in bun_order)

    def list_bun_classes(self):
        return [bun['bun_class'] for bun in self._buns.find({}, {'bun_class': 1})]

    # -------------- internal functions --------------

    def _calculate_spares(self):
        current_bun_order = self._get_order(lambda _: True)
        if 'Roeggelchen' in current_bun_order and (current_bun_order['Roeggelchen'] % 2) == 1:
            return ['Roeggelchen', 'Weizen']
        return ['Weizen', 'Weizen']

    def _get_mett(self, bun):  # TODO change to use of names not id
        return float(self._buns.find_one({'_id': bun}, {'mett': 1})['mett'])

    def _get_account_id_from_name(self, name):  # TODO change to use of names not id
        mett_account = self._account.find_one({'name': name})
        if not mett_account:
            raise StorageException('No matching user record')
        return mett_account['_id']

    def _get_account_name_from_id(self, account_id):  # TODO change to use of names not id
        mett_account = self._account.find_one({'_id': account_id})
        if not mett_account:
            raise StorageException('No matching user record')
        return mett_account['name']

    def _resolve_bun(self, item):  # TODO change to use of names not id
        if isinstance(item, str):
            bun_class = self._buns.find_one({'bun_class': item}, {'_id': 1})
            return bun_class['_id']
        bun_class = self._buns.find_one({'_id': item}, {'bun_class': 1})
        return bun_class['bun_class']

    def _get_current_order(self):
        current_order = self._alt_order.find_one({'processed': False})
        if not current_order:
            raise StorageException('No current order')
        return current_order

    def _charge_bun(self, account, bun):  # TODO change to use of names not id
        bun_price = self._buns.find_one({'_id': bun})
        self._account.update_one({'_id': account}, {'$inc': {'balance': 0 - float(bun_price['price'])}})

    # -------------- internal functions --------------

    def create_order_alt(self, expiry_date):
        if self._is_expired(expiry_date):
            raise StorageException('Please enter date that hasn\'t expired yet')
        if self.active_order_exists():
            raise StorageException('No new order can be initialized while another one is active')
        return self._alt_order.insert_one({'expiry_date': expiry_date, 'processed': False, 'orders': []}).inserted_id

    def current_order_is_expired(self):
        if not self.active_order_exists():
            raise StorageException('There is no active order')
        return self._is_expired(self._get_current_order()['expiry_date'])

    def _is_expired(self, expiry_date):
        expiry_time = self._config.get('DEFAULT', 'expiry_time').strip()
        return datetime.datetime.strptime('{} {}'.format(expiry_date, expiry_time), '%Y-%m-%d %H:%M:%S') > datetime.datetime.now()
