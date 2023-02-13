from configparser import ConfigParser
from pathlib import Path

import pytest

from app.app_setup import AppSetup
from database.interface import MettInterface
from test.unit.common import TestUser  # pylint: disable=wrong-import-order


@pytest.fixture(scope='function')
def config_for_tests():
    config = ConfigParser()
    config.read(str(Path(Path(__file__).parent.parent, 'config', 'app.config')))
    config.set('Runtime', 'testing', 'true')
    config.set('Database', 'database_path', ':memory:')
    config.set('Mett', 'default_buns', 'Weizen, Roggen')
    config.set('Mett', 'half_buns', '')
    return config


@pytest.fixture(scope='function')
def app(config_for_tests):
    return AppSetup(config=config_for_tests)


@pytest.fixture(scope='function')
def interface(app, config_for_tests):
    interface = MettInterface(config_for_tests)
    _initialize_database(interface, app)
    return interface


@pytest.fixture(scope='function')
def combined_app(app, interface):
    app.database = interface
    app.mett_store = interface
    return app


@pytest.fixture(scope='function')
def client(app):  # pylint: disable=redefined-outer-name
    _initialize_database(app.database, app)
    return app.app.test_client()


def _initialize_database(interface, app):
    interface.create_tables()
    interface.initialize_bun_classes()

    with app.app.app_context():
        interface.create_user(TestUser.name, TestUser.password)

    interface.create_role('role')
