from configparser import ConfigParser
from pathlib import Path


def config_for_tests(tmpdir=None):
    config = ConfigParser()
    config.read(str(Path(Path(__file__).parent.parent.parent, 'config', 'app.config')))

    config.set('Runtime', 'testing', 'true')
    config.set('Database', 'main_database', 'mett_test')

    if tmpdir:
        config.set('Runtime', 'user_database', str(tmpdir.join('user.db')))

    return config
