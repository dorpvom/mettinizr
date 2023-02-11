from collections import namedtuple

from flask_login import UserMixin

Role = namedtuple('Role', ['name'])


class SecurityUser(UserMixin):
    def __init__(self, name, password, roles):
        self.name = name
        self.password = password
        self.roles = [Role(name=role) for role in roles]

        self.id = self.name


Purchase = namedtuple('Purchase', ['p_id', 'account', 'price', 'purpose', 'timestamp', 'processed'])
Order = namedtuple('Order', ['processed', 'expiry_date', 'buns'])
OrderedBun = namedtuple('OrderedBun', ['bun', 'account', 'order'])
