#!/usr/bin/env python3

import argparse
import getpass
import sys

from passlib.context import CryptContext

from app.app_setup import AppSetup
from database.mett_store import MettStore


def setup_argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action='version', version='mettinizr User Management (METTUM) 0.1')
    parser.add_argument('-C', '--config_file', help='set path to config File', default='config/app.config')
    return parser.parse_args()


def get_input(message, max_len=25):
    while True:
        user_input = input(message)
        if len(user_input) > max_len:
            raise ValueError('Error: input too long (max length: {})'.format(max_len))
        else:
            return user_input


def choose_action():
    print('\nPlease choose an action (use "help" for a list of available actions)')
    chosen_action = input('action: ')
    return chosen_action


def password_is_legal(password: str) -> bool:
    if not password:
        return False
    schemes = ['bcrypt', 'des_crypt', 'pbkdf2_sha256', 'pbkdf2_sha512', 'sha256_crypt', 'sha512_crypt', 'plaintext']
    ctx = CryptContext(schemes=schemes)
    return ctx.identify(password) == 'plaintext'


class Actions:
    @staticmethod
    def help(*_):
        print(
            '\nPlease choose an action:\n'
            '\n\t[create_user]\t\tcreate new user'
            '\n\t[delete_user]\t\tdelete a user'
            '\n\t[create_role]\t\tcreate new role'
            '\n\t[add_role_to_user]\tadd existing role to an existing user'
            '\n\t[remove_role_from_user]\tremove role from user'
            '\n\t[get_apikey_for_user]\tretrieve apikey for existing user'
            '\n\t[help]\t\t\tshow this help'
            '\n\t[exit]\t\t\tclose application'
        )

    @staticmethod
    def _user_exists(app, interface, name):
        with app.app_context():
            user = interface.find_user(email=name)
        return bool(user)

    @staticmethod
    def exit(*_):
        raise EOFError('Quitting ..')

    @staticmethod
    def create_user(app, interface, database, mett_store):
        user = get_input('username: ')
        assert not Actions._user_exists(app, interface, user), 'user must not exist'

        password = getpass.getpass('password: ')
        assert password_is_legal(password), 'password is illegal'

        if not mett_store.account_exists(user):
            mett_store.create_account(user)

        with app.app_context():
            interface.create_user(email=user, password=password)
            database.session.commit()

    @staticmethod
    def _role_exists(app, interface, role):
        with app.app_context():
            exists = interface.find_role(role)
        return bool(exists)

    @staticmethod
    def create_role(app, interface, database, _):
        role = get_input('role name: ')
        with app.app_context():
            interface.create_role(name=role)
            database.session.commit()

    @staticmethod
    def add_role_to_user(app, interface, database, _):
        user = get_input('username: ')
        assert Actions._user_exists(app, interface, user), 'user must exists before adding it to role'

        role = get_input('role name: ')
        assert Actions._role_exists(app, interface, role), 'role must exists before user can be added'

        with app.app_context():
            interface.add_role_to_user(user=interface.find_user(email=user), role=role)
            database.session.commit()

    @staticmethod
    def remove_role_from_user(app, interface, database, _):
        user = get_input('username: ')
        assert Actions._user_exists(app, interface, user), 'user must exists before adding it to role'

        role = get_input('role name: ')
        assert Actions._role_exists(app, interface, role), 'role must exists before user can be added'

        with app.app_context():
            interface.remove_role_from_user(user=interface.find_user(email=user), role=role)
            database.session.commit()

    @staticmethod
    def delete_user(app, interface, database, _):
        user = get_input('username: ')
        assert Actions._user_exists(app, interface, user), 'user must exists before adding it to role'

        with app.app_context():
            interface.delete_user(user=interface.find_user(email=user))
            database.session.commit()


LEGAL_ACTIONS = [action for action in dir(Actions) if not action.startswith('_')]


def prompt_for_actions(app, store, database, mett_store):
    # pylint: disable=anomalous-backslash-in-string
    print('''                             _   _   _       _
              _ __ ___   ___| |_| |_(_)_ __ (_)_____ __
             | '_ ` _ \ / _ \ __| __| | '_ \| |_  / '__|
             | | | | | |  __/ |_| |_| | | | | |/ /| |
             |_| |_| |_|\___|\__|\__|_|_| |_|_/___|_|''')

    print('\nWelcome to the mettinizr User Management (METTUM)\n')

    while True:
        try:
            action = choose_action()
        except (EOFError, KeyboardInterrupt):
            break
        if action not in LEGAL_ACTIONS:
            print('error: please choose a legal action.')
        else:
            try:
                acting_function = getattr(Actions, action)
                acting_function(app, store, database, mett_store)
            except AssertionError as assertion_error:
                print('error: {}'.format(assertion_error))
            except EOFError:
                break

    print('\nQuitting ..')


def start_user_management(app_setup):
    mett_store = MettStore(app_setup.config)

    app_setup.user_database.create_all()

    prompt_for_actions(app_setup.app, app_setup.user_interface, app_setup.user_database, mett_store)

    return 0


if __name__ == '__main__':
    sys.exit(start_user_management(AppSetup()))
