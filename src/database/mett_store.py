'''
account: id, name, balance (id private_key)
order: id, expired, orders (orders list of (account, bun), with account foreign_key on account.id and bun foreign_key on price.id)
price: id, bun_class, amount
purchase: id, account, amount, processed (account foreign_key on accound.id)
mett_formula: bun, amount (bun foreign_key on price.id)
'''
import pymongo


class MettStore:

    def __init__(self, mongo_server='127.0.0.1', mongo_port=27018, main_database='mett_main'):
        self._client = pymongo.MongoClient('mongodb://{}:{}'.format(mongo_server, mongo_port), connect=False)
        self._mett_base = self._client[main_database]
        self._account = self._mett_base.account
        self._order = self._mett_base.order
        self._price = self._mett_base.price

    # -------------- admin functions --------------

    def book_money(self, account, amount):
        # Increase balance of account by amount
        pass

    def assign_spare(self, account, bun_class):
        # add (account, bun_class) to order
        pass

    def list_accounts(self):
        # return list of (accound.id, account.name) tuples
        pass

    def create_order(self):  # throws Excreption on existing non-expired order
        # create new order
        pass

    def expire_order(self):
        # set expire of current order to true and decrease balances according to order
        pass

    def drop_order(self, order):
        # drop order by id
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

    def get_account_information(self, account):
        # get (id, name, balance) for account
        pass

    def order_bun(self, account, bun_class):  # throws Exception if no current order
        # add (account, bun_class) to current order
        pass

    def state_purchase(self, account, amount):
        # add account, amount as non processed purchase
        pass

    def get_order_history(self, account):
        # get list of (order_id, orders) where orders is slice of orders ordered by account
        pass

    def get_current_bun_order(self):
        # get aggregated current bun order
        pass

    def get_current_mett_order(self):
        # generate mett order from bun order
        pass
