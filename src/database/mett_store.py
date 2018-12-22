'''
account: id, name, balance (id private_key)
order: id, expired, orders (orders list of (account, bun), with account foreign_key on account.id and bun foreign_key on price.id)
price: id, bun_class, price, mett
purchase: id, account, price, processed (account foreign_key on accound.id)
'''
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
        self._price = self._mett_base.price

        self._init_tables()

    def _init_tables(self):
        if self._price.find().count() == 0:
            for bun in self._config.get('Mett', 'default_buns').split(','):
                self._price.insert_one({'bun_class': bun.strip(), 'price': self._config.get('Mett', 'default_price'), 'mett': self._config.get('Mett', 'default_grams')})

    # -------------- admin functions --------------

    def create_account(self, name):
        if self.account_exists(name):
            raise StorageException('Account {} exists'.format(name))
        result = self._account.insert_one({'name': name, 'balance': 0.0})
        return result.inserted_id

    def book_money(self, account, amount):
        # Increase balance of account by amount
        self._account.update_one({'_id': self._get_account_id_from_name(account)}, {'$inc': {'balance': amount}})

    def assign_spare(self, account, bun_class):
        # add (account, bun_class) to order
        pass

    def list_accounts(self):
        # return list of (accound.id, account.name) tuples
        return [(entry['_id'], entry['name']) for entry in self._account.find()]

    def create_order(self):  # throws Excreption on existing non-expired order
        # create new order
        if self.active_order_exists():
            raise StorageException('Only one current order allowed at all time')
        return self._order.insert_one({'expired': False, 'orders': []}).inserted_id

    def expire_order(self):
        # set expire of current order to true and decrease balances according to order
        pass

    def drop_order(self, order=None):
        # drop order by id or current order
        pass

    def list_purchases(self, processed=False):
        # list purchases, if processed is false only those that have not been authorized or declined
        pass

    def authorize_purchase(self, purchase):
        # add purchase.amount to purchase.account.balance
        pass

    def decline_purchase(self, purchase):
        # drop purchase
        pass

    def change_mett_formula(self, bun, amount):
        # set mett_formula.amount for referenced bun
        pass

    # -------------- user functions --------------

    def active_order_exists(self):
        return self._order.find({'expired': False}).count() > 0

    def account_exists(self, name):
        return self._account.find({'name': name}).count() > 0

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
        orders = current_order['orders']
        orders.append((self._get_account_id_from_name(account), self._resolve_bun(bun_class)))
        self._order.update_one({'_id': current_order['_id']}, {'$set': {'orders': orders}})

    def state_purchase(self, account, amount):
        # add account, amount as non processed purchase
        pass

    def get_order_history(self, account):
        # get list of (order_id, orders) where orders is slice of orders ordered by account
        pass

    def get_current_user_buns(self, user):
        # get list of buns ordered by user
        return self._get_order(lambda x: x == self._get_account_id_from_name(user))

    def get_current_bun_order(self):
        # get aggregated current bun order
        return self._get_order(lambda _: True)

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
        return sum(self._get_mett(bun) for _, bun in self._get_current_order()['orders'])

    def list_bun_classes(self):
        return [bun['bun_class'] for bun in self._price.find({}, {'bun_class': 1})]

    # -------------- internal functions --------------

    def _get_mett(self, bun):
        return self._price.find_one({'_id': bun}, {'mett': 1})['mett']

    def _get_account_id_from_name(self, name):
        mett_account = self._account.find_one({'name': name})
        if not mett_account:
            raise StorageException('No matching user record')
        return mett_account['_id']

    def _get_account_name_from_id(self, account_id):
        mett_account = self._account.find_one({'_id': account_id})
        if not mett_account:
            raise StorageException('No matching user record')
        return mett_account['name']

    def _resolve_bun(self, item):
        if isinstance(item ,str):
            bun_class = self._price.find_one({'bun_class': item}, {'_id': 1})
            return bun_class['_id']
        bun_class = self._price.find_one({'_id': item}, {'bun_class': 1})
        return bun_class['bun_class']

    def _get_current_order(self):
        current_order = self._order.find_one({'expired': False})
        if not current_order:
            raise StorageException('No current order')
        return current_order
