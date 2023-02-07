import sys
from typing import List, Union

from passlib.context import CryptContext
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from database.database_objects import BunClassEntry, UserEntry, RoleEntry, SingleOrderEntry, OrderEntry, DepositEntry, PurchaseEntry, PurchaseAuthorizationEntry
from database.database import SQLDatabase, DatabaseError
from datetime import datetime
from flask_security.utils import verify_password, hash_password

from database.offline_objects import Order
from database.user_store import SecurityUser


class MettInterface(SQLDatabase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initialize_bun_classes(self):
        with self.get_read_write_session() as session:
            if not self.list_bun_classes():
                for bun in self.config.get('Mett', 'default_buns').split(','):
                    bun_entry = BunClassEntry(
                        name=bun.strip(),
                        price=self.config.getfloat('Mett', 'default_price'),
                        mett=self.config.getfloat('Mett', 'default_grams')
                    )
                    session.add(bun_entry)

    def create_user(self, name: str, password: str, is_hashed: bool = False):
        if self.user_exists(name):
            raise DatabaseError('User already exists')
        if not is_hashed and not password_is_legal(password):
            raise DatabaseError('Illegal password. Ask admin for password rules.')
        with self.get_read_write_session() as session:
            new_entry = UserEntry(
                name=name,
                password=password if is_hashed else hash_password(password),
                balance=0.0
            )
            session.add(new_entry)
            return new_entry

    def get_user(self, name) -> Union[SecurityUser, None]:
        with self.get_read_write_session() as session:
            if not self.user_exists(name):
                return None

            user_entry = session.get(UserEntry, name)
            return SecurityUser(name=user_entry.name, password=user_entry.password, roles=[role.name for role in user_entry.roles])

    def get_balance(self, name) -> Union[float, None]:
        return self._get_user_attribute(name, 'balance')

    def _get_user_attribute(self, username: str, attribute: str):
        with self.get_read_write_session() as session:
            if not self.user_exists(username):
                return None

            user = session.get(UserEntry, username)
            return getattr(user, attribute)

    def add_role_to_user(self, user: str, role: str):
        if not self.user_exists(user) or not self.role_exists(role):
            raise DatabaseError('User or role does not exist')
        with self.get_read_write_session() as session:
            user_entry = session.get(UserEntry, user)
            if role in [role.name for role in user_entry.roles]:
                raise DatabaseError('User already has role')
            user_entry.roles.append(session.get(RoleEntry, role))

    def create_role(self, name: str):
        with self.get_read_write_session() as session:
            new_entry = RoleEntry(name=name)
            session.add(new_entry)
            return new_entry

    def get_role(self, name):
        with self.get_read_write_session() as session:
            return session.get(RoleEntry, name)

    def role_exists(self, name: str) -> bool:
        with self.get_read_write_session() as session:
            return session.get(RoleEntry, name) is not None

    def user_exists(self, name: str) -> bool:
        with self.get_read_write_session() as session:
            return session.get(UserEntry, name) is not None

    def add_bun_class(self, name, price, mett_amount):
        with self.get_read_write_session() as session:
            new_entry = BunClassEntry(name=name, price=price, mett=mett_amount)
            session.add(new_entry)

    def bun_class_exists(self, name):
        with self.get_read_write_session() as session:
            return session.get(BunClassEntry, name) is not None

    def list_bun_classes(self) -> list:
        with self.get_read_write_session() as session:
            classes = session.execute(select(BunClassEntry.name))
            return list(classes.scalars())

    def create_order(self, expiry_date: str):
        with self.get_read_write_session() as session:
            if self._is_expired(expiry_date):
                raise DatabaseError('Please enter date that hasn\'t expired yet')
            if self.active_order_exists():
                raise DatabaseError('No new order can be initialized while another one is active')

            new_entry = OrderEntry(
                expiry_date=datetime.strptime(expiry_date, '%Y-%m-%d').date(),
                processed=False
            )
            session.add(new_entry)
            return new_entry

    def active_order_exists(self):
        with self.get_read_write_session() as session:
            query = select(OrderEntry._id).filter(OrderEntry.processed == False)
            return session.execute(query).first() is not None

    def _is_expired(self, expiry_date):
        expiry_time = self.config.get('DEFAULT', 'expiry_time').strip()
        return datetime.strptime('{} {}'.format(expiry_date, expiry_time), '%Y-%m-%d %H:%M:%S') < datetime.now()

    def current_order_is_expired(self):
        with self.get_read_write_session() as session:
            if not self.active_order_exists():
                raise DatabaseError('There is no active order')
            return self._is_expired(self._get_current_order(session).expiry_date)

    @staticmethod
    def _get_current_order(session) -> OrderEntry:
        return session.execute(select(OrderEntry).where(OrderEntry.processed == False)).one_or_none()[0]

    def drop_current_order(self):
        # drop current order
        with self.get_read_write_session() as session:
            session.execute(delete(OrderEntry).where(OrderEntry.processed == False))

    def order_bun(self, user: str, bun_class: str):
        with self.get_read_write_session() as session:
            order = self._get_current_order(session)
            bun = session.get(BunClassEntry, bun_class)
            user = session.get(UserEntry, user)
            entry = SingleOrderEntry(account=user.name, bun=bun.name, order=order._id)
            session.add(entry)

    def process_order(self):
        # set expire of current order to true and decrease balances according to order
        with self.get_read_write_session() as session:
            order = self._get_current_order(session)
            for bun in order.buns:
                self._charge_bun(session, bun.account, bun.bun)

            order.processed = True
            session.commit()

    def _charge_bun(self, session, account, bun):
        price = session.get(BunClassEntry, bun).price
        user = session.get(UserEntry, account)
        user.balance -= price

    def change_balance(self, account, amount, admin):
        # Store which admin has allowed the balance change
        with self.get_read_write_session() as session:
            user = session.get(UserEntry, account)
            user.balance += amount
            session.commit()

    def list_accounts(self):
        with self.get_read_write_session() as session:
            accounts = session.execute(select(UserEntry).order_by(UserEntry.name)).all()
            return [account[0].name for account in accounts]

    def list_purchases(self, processed):
        # list purchases, if processed is false only those that have not been authorized or declined
        raise NotImplementedError()

    def authorize_purchase(self, purchase_id, admin):
        # add purchase.amount to purchase.account.balance
        raise NotImplementedError()

    def decline_purchase(self, purchase_id, admin):
        # drop purchase
        raise NotImplementedError()

    def list_users(self):
        raise NotImplementedError()

    def list_roles(self):
        raise NotImplementedError()

    def password_is_correct(self, user_name, password):
        stored_password = self.get_user(user_name).password
        return verify_password(password, stored_password)

    def change_password(self, user_name, password):
        raise NotImplementedError()

    def find_user(self, id):
        return self.get_user(id)

    def find_role(self, role):
        raise NotImplementedError()

    def remove_role_from_user(self, user, role):
        raise NotImplementedError()

    def toggle_active(self, user):
        raise NotImplementedError()

    def deactivate_user(self, user):
        raise NotImplementedError()

    def activate_user(self, user):
        raise NotImplementedError()

    def find_or_create_role(self, name, **kwargs):
        raise NotImplementedError()

    def delete_user(self, user: str):
        raise NotImplementedError()

    def commit(self):
        pass

    def get_deposits(self):
        raise NotImplementedError()
    def change_mett_formula(self, bun, amount):
        # set mett amount for referenced bun
        raise NotImplementedError()

    def change_bun_price(self, bun, price):
        # set mett price for referenced bun
        raise NotImplementedError()

    def assign_spare(self, bun_class, user):
        raise NotImplementedError()

    def reroute_bun(self, bun_class, user, target):
        # Change order from one user to another
        raise NotImplementedError()

    def state_purchase(self, account, amount, purpose):
        # add account, amount, purpose as non processed purchase
        raise NotImplementedError()

    def get_order_history(self, user):
        # get list of (order_id, orders) where orders is slice of orders ordered by account
        raise NotImplementedError()

    def get_current_user_buns(self, user):
        # get list of buns ordered by user
        raise NotImplementedError()

    def get_current_bun_order(self):
        # get aggregated current bun order
        raise NotImplementedError()

    def get_current_mett_order(self):
        # generate mett order from bun order
        raise NotImplementedError()

    def list_bun_classes_with_price(self) -> dict:
        raise NotImplementedError()

    def get_all_order_information(self) -> list:
        raise NotImplementedError()


def password_is_legal(password: str) -> bool:
    if not password:
        return False
    schemes = ['bcrypt', 'des_crypt', 'pbkdf2_sha256', 'pbkdf2_sha512', 'sha256_crypt', 'sha512_crypt', 'plaintext']
    ctx = CryptContext(schemes=schemes)
    return ctx.identify(password) == 'plaintext'
