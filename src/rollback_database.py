import json
import sys
from pathlib import Path

from bson import ObjectId
from flask import Flask

from app.app_setup import AppSetup
from database.mett_store import MettStore, StorageException
from database.user_store import UserRoleDatabase


def error(exception):
    print('[Error] {}'.format(exception))


def build_object_id(id_representation):
    if not id_representation.startswith('ObjectId'):
        raise ValueError('ObjectId not formatted correctly')

    prefix_length = len('ObjectId("')
    id_length = 24

    string_id = id_representation[prefix_length:prefix_length + id_length]

    return ObjectId(string_id)


def restore_roles(user_interface: UserRoleDatabase, roles: list):
    for role in roles:
        user_interface.create_role(name=role)


def restore_accounts(user_interface: UserRoleDatabase, mett_store: MettStore, app: Flask, users: list, accounts: list):
    for name, password, roles in users:
        with app.app_context():
            user_interface.create_user(name=name, password=password, roles=roles, is_hashed=True)

    for account in accounts:
        mett_store.create_account(account['name'])
        mett_store.change_balance(account['name'], account['balance'], 'rollback')


def restore_buns(mett_store: MettStore, buns: list):
    for bun in buns:
        mett_store.change_mett_formula(bun['bun_class'], bun['mett'])
        mett_store.change_bun_price(bun['bun_class'], bun['price'])


def restore_orders(mett_store: MettStore, orders: list, accounts: list, buns: list):
    for order in orders:
        if _is_old_database_order(order):
            _restore_old_order(mett_store, order, accounts, buns)
        else:
            _restore_new_order(mett_store, order)


def _restore_new_order(mett_store, order):
    order.pop('_id')
    mett_store._order.insert_one(order)  # pylint: disable=protected-access


def _restore_old_order(mett_store, order, accounts, buns):
    order.pop('_id')
    order['orders'] = [
        [
            _replace_id_by_value(user_id, accounts, 'name'),
            _replace_id_by_value(bun_id, buns, 'bun_class')
        ] for user_id, bun_id in order['orders']
    ]
    mett_store._order.insert_one(order)  # pylint: disable=protected-access


def _replace_id_by_value(original, reference_list, key):
    for reference in reference_list:
        if reference['_id'] == original:
            return reference[key]
    raise ValueError('Could not match all {}s'.format(key))


def _is_old_database_order(order):
    if not order['orders']:
        return False
    return order['orders'][0][0].startswith('ObjectId')


def restore_purchases_and_deposits(mett_store: MettStore, deposits: list, purchases: list):
    for deposit in deposits:
        deposit.pop('_id')
        mett_store._deposit.insert_one(deposit)  # pylint: disable=protected-access

    for purchase in purchases:
        mett_store._purchase.insert_one(format_purchase(purchase))  # pylint: disable=protected-access


def format_purchase(purchase):
    purchase.pop('_id')
    if isinstance(purchase['processed'], bool):
        purchase['processed'] = {
            'authorized': purchase['processed'],
            'at': None if not purchase['processed'] else '0.0',
            'by': None if not purchase['processed'] else 'rollback'
        }
    return purchase


def rollback(mett_store, user_store, app):
    '''
    Structure
    {
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
    '''

    backup_json = Path('mett.backup.json').read_bytes()
    backup_data = json.loads(backup_json)

    try:
        restore_roles(user_store, backup_data['auth']['role'])
        restore_accounts(user_store, mett_store, app, backup_data['auth']['user'], backup_data['mett']['account'])
        restore_buns(mett_store, backup_data['mett']['bun'])
        restore_orders(mett_store, backup_data['mett']['order'], backup_data['mett']['account'], backup_data['mett']['bun'])
        restore_purchases_and_deposits(mett_store, backup_data['mett']['deposit'], backup_data['mett']['purchases'])
    except StorageException as exception:
        print(
            '[Error] {}. It seems you are trying to rollback into a none empty database. '
            'That\'s foolish, so we don\'t support it.'.format(exception)
        )


def setup_rollback(app):
    rollback(app.mett_store, app.database, app.app)
    return 0


if __name__ == '__main__':
    sys.exit(setup_rollback(AppSetup()))
