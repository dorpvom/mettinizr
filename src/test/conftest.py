from configparser import ConfigParser
from pathlib import Path

import pytest


@pytest.fixture(scope='function')
def config_for_tests():
    config = ConfigParser()
    config.read(str(Path(Path(__file__).parent.parent, 'config', 'app.config')))
    config.set('Runtime', 'testing', 'true')
    config.set('Database', 'database_path', ':memory:')
    config.set('Mett', 'default_buns', 'Weizen, Roggen')
    return config
