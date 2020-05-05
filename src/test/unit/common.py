from configparser import ConfigParser
from contextlib import contextmanager
from pathlib import Path

HAS_EXPIRED, HAS_NOT_EXPIRED = '2000-01-01', '2099-01-01'


class MockUser:
    name = 'mock_user_name'
    password = 'old_password'
    is_authenticated = True
    roles = []


def config_for_tests(tmpdir=None):
    config = ConfigParser()
    config.read(str(Path(Path(__file__).parent.parent.parent, 'config', 'app.config')))

    config.set('Runtime', 'testing', 'true')
    config.set('Runtime', 'behind_proxy', 'false')
    config.set('Database', 'main_database', 'mett_test')
    config.set('User', 'default_role', 'name_that_is_not_used_in_tests')

    if tmpdir:
        config.set('Runtime', 'user_database', 'sqlite:///{}'.format(tmpdir.join('user.db')))

    return config
