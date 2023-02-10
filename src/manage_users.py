#!/usr/bin/env python3

import getpass
import sys

from app.app_setup import AppSetup
from database.user_store import password_is_legal


class DatabaseError(Exception):
    pass


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
            '\n\t[help]\t\t\tshow this help'
            '\n\t[exit]\t\t\tclose application'
        )

    @staticmethod
    def create_user(interface, app):
        user = get_input('username: ')
        if interface.user_exists(user):
            raise DatabaseError('user must not exist')

        password = getpass.getpass('password: ')
        if not password_is_legal(password):
            raise DatabaseError('password is illegal')

        with app.app_context():
            interface.create_user(name=user, password=password)

    @staticmethod
    def create_role(interface, _):
        role = get_input('role name: ')
        if interface.role_exists(role):
            raise DatabaseError('role must not exist')

        interface.create_role(name=role)

    @staticmethod
    def add_role_to_user(interface, _):
        user = get_input('username: ')
        if not interface.user_exists(user):
            raise DatabaseError('user must exists before adding it to role')

        role = get_input('role name: ')
        if not interface.role_exists(role):
            raise DatabaseError('role must exists before user can be added')

        interface.add_role_to_user(user=user, role=role)

    @staticmethod
    def remove_role_from_user(interface, _):
        user = get_input('username: ')
        if not interface.user_exists(user):
            raise DatabaseError('user must exists before removing role from it')

        role = get_input('role name: ')
        if not interface.role_exists(role):
            raise DatabaseError('role must exists before removing it from user')

        interface.remove_role_from_user(user=user, role=role)

    @staticmethod
    def delete_user(interface, _):
        user = get_input('username: ')
        if not interface.user_exists(user):
            raise DatabaseError('user must exists before deleting it')

        interface.delete_user(user=user)

    @staticmethod
    def exit(*_):
        raise EOFError('Quitting ..')


LEGAL_ACTIONS = [action for action in dir(Actions) if not action.startswith('_')]


def prompt_for_actions(app_setup):
    print(r'''                             _   _   _       _
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
                acting_function(app_setup.user_interface, app_setup.app)
            except (DatabaseError, ValueError) as error:
                print('error: {}'.format(error))
            except EOFError:
                break

    print('\nQuitting ..')
    return 0


if __name__ == '__main__':
    sys.exit(prompt_for_actions(AppSetup()))
