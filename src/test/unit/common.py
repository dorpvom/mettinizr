from configparser import ConfigParser
from pathlib import Path

HAS_EXPIRED, HAS_NOT_EXPIRED = '2000-01-01', '2099-01-01'


class MockUser:
    email = 'mock_user_name'
    is_authenticated = True


def config_for_tests(tmpdir=None):
    config = ConfigParser()
    config.read(str(Path(Path(__file__).parent.parent.parent, 'config', 'app.config')))

    config.set('Runtime', 'testing', 'true')
    config.set('Database', 'main_database', 'mett_test')

    if tmpdir:
        config.set('Runtime', 'user_database', 'sqlite:///{}'.format(tmpdir.join('user.db')))

    return config
