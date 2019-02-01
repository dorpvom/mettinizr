import os
from configparser import ConfigParser
from pathlib import Path

from flask import Flask

from app.admin import AdminRoutes
from app.orders import OrderRoutes
from app.dashboard import DashboardRoutes
from app.profile import ProfileRoutes
from app.security.authentication import add_flask_security_to_app
from app.user import UserRoutes
from database.mett_store import MettStore


class AppSetup:
    def __init__(self, config=None):
        if not config:
            self.config = ConfigParser()
            self.config.read(str(Path(Path(__file__).parent.parent, 'config', 'app.config')))
        else:
            self.config = config

        self.app = Flask(__name__)
        self.app.secret_key = os.urandom(24)

        self.user_database, self.user_interface = add_flask_security_to_app(self.app, self.config)

        self.mett_store = MettStore(config=self.config)

        OrderRoutes(self.app, self.config, self.mett_store)
        DashboardRoutes(self.app, self.config, self.mett_store)
        AdminRoutes(self.app, self.config, self.mett_store)
        ProfileRoutes(self.app, self.config, self.user_database, self.user_interface)
        UserRoutes(self.app, self.config, self.mett_store, self.user_interface)
