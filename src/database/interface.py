from typing import List

from passlib.context import CryptContext

from database.objects import BunClassEntry, UserEntry, RoleEntry, SingleOrderEntry, OrderEntry, DepositEntry, PurchaseEntry, PurchaseAuthorizationEntry
from database.database import SQLDatabase, DatabaseError
from datetime import date
from flask_security.utils import verify_password, hash_password


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

    def create_order(self, expiry_date: float):
        with self.get_read_write_session() as session:
            new_entry = OrderEntry(expiry_data=date.fromtimestamp(expiry_date), processed=False)
            session.add(new_entry)
            return new_entry

def password_is_legal(password: str) -> bool:
    if not password:
        return False
    schemes = ['bcrypt', 'des_crypt', 'pbkdf2_sha256', 'pbkdf2_sha512', 'sha256_crypt', 'sha512_crypt', 'plaintext']
    ctx = CryptContext(schemes=schemes)
    return ctx.identify(password) == 'plaintext'
