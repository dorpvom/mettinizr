from collections import namedtuple

from flask_security import UserMixin, RoleMixin


class Role(RoleMixin):
    def __init__(self, name):
        self.name = name
        super().__init__()


class SecurityUser(UserMixin):
    def __init__(self, name, password, roles):
        self.name = name
        self.password = password
        self.roles = [Role(name=role) for role in roles]
        self.active = True
        self.fs_uniquifier = name

        self.id = self.name


Purchase = namedtuple('Purchase', ['p_id', 'account', 'price', 'purpose', 'timestamp', 'processed'])
Order = namedtuple('Order', ['processed', 'expiry_date', 'buns'])
OrderedBun = namedtuple('OrderedBun', ['bun', 'account', 'order'])
