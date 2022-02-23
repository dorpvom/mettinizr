from pathlib import Path
from configparser import ConfigParser

from app.app_setup import AppSetup
from database.interface import MettInterface
from time import time


DEFAULT_CONFIG_FILE = Path(Path(__file__).parent, 'config', 'app.config')


def load_default_config():
    config = ConfigParser()
    config.read(str(DEFAULT_CONFIG_FILE))
    return config


def init_database():
    config = load_default_config()
    app = AppSetup(config=config)
    interface = MettInterface(config)
    interface.create_tables()

    if not interface.role_exists(config.get('User', 'default_role')):
        interface.create_role(config.get('User', 'default_role'))

    if not interface.user_exists(config.get('Database', 'default_user')):
        with app.app.app_context():
            interface.create_user(
                config.get('Database', 'default_user'),
                config.get('Database', 'default_password'),
            )
        interface.add_role_to_user(
            config.get('Database', 'default_user'),
            config.get('User', 'default_role')
        )

    for default_bun in config.get('Mett', 'default_buns').split(','):
        if not interface.bun_class_exists(default_bun.strip()):
            interface.add_bun_class(
                default_bun.strip(),
                config.getfloat('Mett', 'default_price'),
                config.getfloat('Mett', 'default_grams')
            )

    # interface.create_order(expiry_date=time() + 60.0 * 60.0 * 24.0 * 7.0)
    exit(0)


if __name__ == '__main__':
    init_database()
    exit(0)
