import os
from configparser import ConfigParser
from pathlib import Path

from flask import Flask

from app.orders import OrderRoutes
from app.dashboard import DashboardRoutes
from app.security.authentication import add_flask_security_to_app

CONFIG = ConfigParser()
CONFIG.read(str(Path(Path(__file__).parent.parent, 'config', 'app.config')))

APP = Flask(__name__)
APP.secret_key = os.urandom(24)

USER_DATABASE, USER_INTERFACE = add_flask_security_to_app(APP, CONFIG)

OrderRoutes(APP, CONFIG)
DashboardRoutes(APP, CONFIG)
