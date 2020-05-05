import json
import sys
from collections import namedtuple
from pathlib import Path

from app.app_setup import AppSetup
from database.mett_store import MettStore

User = namedtuple('User', ['email', 'password', 'roles'])


def filter_roles(database, user, roles):
    return [
        role for role in roles if role in user.roles
    ]


def replace_object_ids(iterable):
    for entry in iterable:
        entry['_id'] = str(entry['_id'])
        yield entry


def backup(app, user_store, mett_store: MettStore, database):
    with app.app_context():
        roles = [role.name for role in user_store.list_roles()]
        users = [User(email=user.email, password=user.password, roles=filter_roles(database, user, roles)) for user in user_store.list_users()]

    accounts = list(replace_object_ids(mett_store._account.find()))
    orders = list(replace_object_ids(mett_store._order.find()))
    buns = list(replace_object_ids(mett_store._buns.find()))
    purchases = list(replace_object_ids(mett_store._purchase.find()))
    deposits = list(replace_object_ids(mett_store._deposit.find()))

    backup = {
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

    backup_json = json.dumps(backup)
    Path('mett.backup.json').write_text(backup_json)


def start_backup(app_setup):
    backup(app_setup.app, app_setup.user_interface, app_setup.mett_store, app_setup.user_database)
    return 0


if __name__ == '__main__':
    sys.exit(start_backup(AppSetup()))
