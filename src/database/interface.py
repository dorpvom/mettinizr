from typing import List

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.database_objects import BunClassEntry, UserEntry, RoleEntry, SingleOrderEntry, OrderEntry, DepositEntry, PurchaseEntry, PurchaseAuthorizationEntry
from database.database import SQLDatabase, DatabaseError
from datetime import date, datetime
from flask_security.utils import verify_password, hash_password

from database.offline_objects import Order


class MettInterface(SQLDatabase):
    def create_user(self, name: str, password: str, is_hashed: bool = False):
        if self.user_exists(name):
            raise DatabaseError('User already exists')
        if not is_hashed and not password_is_legal(password):
            raise DatabaseError('Illegal password. Ask admin for password rules.')
        with self.get_read_write_session() as session:
            new_entry = UserEntry(name=name, password=password if is_hashed else hash_password(password))
            session.add(new_entry)
            return new_entry

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

    def create_order(self, expiry_date: str):
        with self.get_read_write_session() as session:
            if self._is_expired(expiry_date):
                raise DatabaseError('Please enter date that hasn\'t expired yet')
            if self.active_order_exists():
                raise DatabaseError('No new order can be initialized while another one is active')

            new_entry = OrderEntry(expiry_data=date.fromisoformat(expiry_date), processed=False)
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
    def _get_current_order(session: Session) -> Order:
        result = session.execute(select(OrderEntry.processed, OrderEntry.expiry_data).filter(OrderEntry.processed == False)).one_or_none()
        if result is None:
            raise DatabaseError('No current order')
        return Order(*result, [])  # FIXME Solve buns problem


def password_is_legal(password: str) -> bool:
    if not password:
        return False
    schemes = ['bcrypt', 'des_crypt', 'pbkdf2_sha256', 'pbkdf2_sha512', 'sha256_crypt', 'sha512_crypt', 'plaintext']
    ctx = CryptContext(schemes=schemes)
    return ctx.identify(password) == 'plaintext'
