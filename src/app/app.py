import os
from pathlib import Path
from configparser import ConfigParser
from app.security.authentication import add_flask_security_to_app
from flask import Flask


CONFIG = ConfigParser()
CONFIG.read(Path(Path(__file__).parent.parent, 'config', 'app.config'))

APP = Flask(__name__)
APP.secret_key = os.urandom(24)

USER_DATABASE, USER_INTERFACE = add_flask_security_to_app(APP, CONFIG)
