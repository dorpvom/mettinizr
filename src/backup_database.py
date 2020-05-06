import json
import sys
from collections import namedtuple
from pathlib import Path

from bson import ObjectId

from app.app_setup import AppSetup
from database.mett_store import MettStore

User = namedtuple('User', ['email', 'password', 'roles'])


def filter_roles(user, roles):
    return [
        role for role in roles if role in user.roles
    ]


class MongoEncoder(json.JSONEncoder):
    def default(self, obj: ObjectId):
        if isinstance(obj, ObjectId):
            return obj.__repr__()
        return json.JSONEncoder.default(self, obj)


def backup(app, user_store, mett_store: MettStore):
    with app.app_context():
        try:  # Old user database
            roles = [role.name for role in user_store.list_roles()]
            users = [User(email=user.email, password=user.password, roles=filter_roles(user, roles)) for user in user_store.list_users()]
        except AttributeError:  # New user database
            roles = [role['name'] for role in user_store.list_roles()]
            users = [
                User(email=user.name, password=user.password, roles=[role.name for role in user.roles])
                for user in [
                    user_store.get_user(user['name']) for user in user_store.list_users()
                ]
            ]

    accounts = list(mett_store._account.find()) if getattr(mett_store, '_account', None) else []
    orders = list(mett_store._order.find()) if getattr(mett_store, '_order', None) else []
    buns = list(mett_store._buns.find()) if getattr(mett_store, '_buns', None) else []
    purchases = list(mett_store._purchase.find()) if getattr(mett_store, '_purchase', None) else []
    deposits = list(mett_store._deposit.find()) if getattr(mett_store, '_deposit', None) else []

    backup_data = {
        'auth': {
            'user': users,
            'role': roles
        },
        'mett': {
            'account': accounts,
            'order': orders,
            'bun': buns,
            'purchases': purchases,
            'deposit': deposits
        }
    }

    backup_json = json.dumps(backup_data, cls=MongoEncoder)
    Path('mett.backup.json').write_text(backup_json)


def start_backup(app_setup):
    backup(app_setup.app, app_setup.user_interface, app_setup.mett_store)
    return 0


if __name__ == '__main__':
    sys.exit(start_backup(AppSetup()))
