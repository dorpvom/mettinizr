from typing import List

from flask_login import UserMixin
from flask_security.utils import verify_password, hash_password
from passlib.context import CryptContext
from pymongo import MongoClient

from database.mett_store import StorageException
from collections import namedtuple

Role = namedtuple('Role', ['name'])


class SecurityUser(UserMixin):
    def __init__(self, name, password, roles):
        self.name = name
        self.password = password
        self.roles = [Role(name=role) for role in roles]

        self.id = self.name


class UserRoleDatabase:
    # FIXME UseEverywhere

    def __init__(self, config):
        self._config = config

        self._client = MongoClient(
            'mongodb://{}:{}'.format(self._config.get('Database', 'mongo_server'), self._config.get('Database', 'mongo_port')),
            connect=False
        )
        self._mett_base = self._client[self._config.get('Database', 'main_database')]

        self._user = self._mett_base.user
        self._role = self._mett_base.role

    def list_users(self):
        return list(self._user.find({}, {'name': 1, 'roles': 1}))

    def list_roles(self):
        return list(self._role.find())

    def password_is_correct(self, user_name, password):
        stored_password = self.get_user(user_name).password
        return verify_password(password, stored_password)

    def change_password(self, user_name, password):
        if not self.user_exists(user_name):
            raise StorageException('User does not exist')
        if not password_is_legal(password):
            raise StorageException('Illegal password. Ask admin for password rules.')
        self._user.update_one({'name': user_name}, {'$set': {'password': hash_password(password)}})

    def user_exists(self, user_name):
        return self._user.find({'name': user_name}).count() == 1

    def role_exists(self, role):
        return self._role.find({'name': role}).count() == 1

    def get_user(self, identifier: str) -> SecurityUser:
        if not self.user_exists(identifier):
            raise StorageException('User does not exist')

        user = self._user.find_one({'name': identifier})
        return SecurityUser(name=user['name'], password=user['password'], roles=user['roles'])

    def find_user(self, id):
        return self.get_user(id)

    def find_role(self, role):
        raise NotImplementedError()

    def add_role_to_user(self, user, role):
        if not self.user_exists(user) or not self.role_exists(role):
            raise StorageException('User or role does not exist')
        roles = [role.name for role in self.get_user(user).roles]
        if role in roles:
            raise StorageException('User already has role')
        roles.append(role)
        self._user.update_one({'name': user}, {'$set': {'roles': roles}})

    def remove_role_from_user(self, user, role):
        if not self.user_exists(user) or not self.role_exists(role):
            raise StorageException('User or role does not exist')
        roles = [role.name for role in self.get_user(user).roles]
        if role not in roles:
            raise StorageException('User doesn\'t have role')
        roles.remove(role)
        self._user.update_one({'name': user}, {'$set': {'roles': roles}})

    def toggle_active(self, user):
        raise NotImplementedError()

    def deactivate_user(self, user):
        raise NotImplementedError()

    def activate_user(self, user):
        raise NotImplementedError()

    def create_role(self, name, **kwargs):
        if kwargs:
            raise NotImplementedError('Other parameters than name, including {} not supported'.format(kwargs))
        if self.role_exists(name):
            raise StorageException('Role already exists')
        self._role.insert_one({'name': name})

    def find_or_create_role(self, name, **kwargs):
        raise NotImplementedError()

    def create_user(self, name: str, password: str, roles: List[str]=None):
        if self.user_exists(name):
            raise StorageException('User already exists')
        if not password_is_legal(password):
            raise StorageException('Illegal password. Ask admin for password rules.')
        if roles and not all(self.role_exists(role) for role in roles):
            raise StorageException('Not all roles in {} exist'.format(roles))
        self._user.insert_one({'name': name, 'password': hash_password(password), 'roles': roles if roles else []})

    def delete_user(self, user: str):
        if not self.user_exists(user):
            raise StorageException('User does not exist')
        self._user.delete_one({'name': user})

    def commit(self):
        pass


def password_is_legal(password: str) -> bool:
    if not password:
        return False
    schemes = ['bcrypt', 'des_crypt', 'pbkdf2_sha256', 'pbkdf2_sha512', 'sha256_crypt', 'sha512_crypt', 'plaintext']
    ctx = CryptContext(schemes=schemes)
    return ctx.identify(password) == 'plaintext'
