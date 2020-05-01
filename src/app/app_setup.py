import os
from configparser import ConfigParser
from pathlib import Path

from flask import Flask

from app.admin import AdminRoutes
from app.dashboard import DashboardRoutes
from app.orders import OrderRoutes
from app.profile import ProfileRoutes
from app.security.authentication import add_flask_security_to_app
from app.user import UserRoutes
from database.mett_store import MettStore


class Filter:
    def __init__(self, app, config):
        self._app = app
        self._config = config

        self._init_filter()

    def _init_filter(self):
        self._app.jinja_env.filters['string_list'] = lambda string_list: ', '.join([str(string) for string in string_list])


class ReverseProxied:
    def __init__(self, app, script_name=None, scheme=None, server=None):
        self.app = app
        self.script_name = script_name
        self.scheme = scheme
        self.server = server

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '') or self.script_name
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]
        scheme = environ.get('HTTP_X_SCHEME', '') or self.scheme
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        server = environ.get('HTTP_X_FORWARDED_SERVER', '') or self.server
        if server:
            environ['HTTP_HOST'] = server
        return self.app(environ, start_response)


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
        UserRoutes(self.app, self.config, self.mett_store, self.user_database, self.user_interface)
        Filter(self.app, self.config)

        if self.config.getboolean('Runtime', 'behind_proxy'):
            self.app.wsgi_app = ReverseProxied(self.app.wsgi_app, script_name='/{}'.format(self.config.get('Runtime', 'proxy_suffix').strip()))
