from collections import namedtuple

'''
    _id = Column(Integer, primary_key=True)
    account = Column(VARCHAR, ForeignKey('user.name'))
    bun = Column(VARCHAR, ForeignKey('bun_class.name'))
    order = Column(Integer, ForeignKey('order._id'))
'''

Order = namedtuple('Order', ['processed', 'expiry_date', 'buns'])
OrderedBun = namedtuple('OrderedBun', ['bun', 'account', 'order'])
