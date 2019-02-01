from functools import wraps

from flask_security import roles_accepted as original_decorator


def roles_accepted(*roles):
    def wrapper(function):
        @wraps(function)
        def decorated_view(*args, **kwargs):
            if not _auth_enabled(args):
                return function(*args, **kwargs)
            return original_decorator(*roles)(function)(*args, **kwargs)
        return decorated_view
    return wrapper


def _get_config_from_endpoint(endpoint_class):
    if getattr(endpoint_class, '_config', None):
        return endpoint_class._config  # pylint: disable=protected-access
    raise AttributeError('There is no accessible config object')


def _auth_enabled(args):
    config = _get_config_from_endpoint(endpoint_class=args[0])
    return not config.getboolean('Runtime', 'testing')
