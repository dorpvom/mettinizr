from sqlalchemy import (
    Boolean, Column, Date, Float, ForeignKey, Integer, Table, PrimaryKeyConstraint
)
from sqlalchemy.dialects.sqlite import VARCHAR
from sqlalchemy.orm import backref, declarative_base, relationship

Base = declarative_base()


role_mapping = Table(
    'role_mapping', Base.metadata,
    Column('user', VARCHAR, ForeignKey('user.name')),
    Column('role', VARCHAR, ForeignKey('role.name'))
)


class RoleEntry(Base):
    __tablename__ = 'role'

    name = Column(VARCHAR, primary_key=True)

    def __repr__(self) -> str:
        return f'Role({self.name})'


class UserEntry(Base):
    __tablename__ = 'user'

    name = Column(VARCHAR, primary_key=True)
    password = Column(VARCHAR, nullable=False)
    balance = Column(Float, nullable=False)
    # fs_uniquifier = Column(VARCHAR, unique=True, nullable=False)

    roles = relationship(
        'RoleEntry',
        secondary='role_mapping',
        backref=backref('users')
    )

    def __repr__(self) -> str:
        return f'User({self.name}, {self.roles})'


class BunClassEntry(Base):
    __tablename__ = 'bun_class'

    name = Column(VARCHAR, primary_key=True)
    price = Column(Float, nullable=False)
    mett = Column(Float, nullable=False)

    def __repr__(self) -> str:
        return f'BunClass({self.name}, {self.price}, {self.mett})'


class SingleOrderEntry(Base):
    __tablename__ = 'single_order'

    _id = Column(Integer, primary_key=True)
    account = Column(VARCHAR, ForeignKey('user.name'))
    bun = Column(VARCHAR, ForeignKey('bun_class.name'))
    order = Column(Integer, ForeignKey('order._id'))

    def __repr__(self) -> str:
        return f'SingleOrder({self.account}, {self.bun})'


class OrderEntry(Base):
    __tablename__ = 'order'

    _id = Column(Integer, primary_key=True)
    expiry_date = Column(Date, nullable=False)
    processed = Column(Boolean, nullable=False)

    buns = relationship(
        'SingleOrderEntry',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'Order({self.expiry_date}, {self.processed}, {self.buns})'


class PurchaseEntry(Base):
    __tablename__ = 'purchase'

    _id = Column(Integer, primary_key=True)
    account = Column(VARCHAR, ForeignKey('user.name'))
    price = Column(Float, nullable=False)
    purpose = Column(VARCHAR, nullable=False)
    timestamp = Column(Date, nullable=False)

    processed = Column(Boolean, nullable=False)
    authorized = Column(Boolean)
    at = Column(Date)
    by = Column(VARCHAR, ForeignKey('user.name'))

    def __repr__(self) -> str:
        return f'Purchase({self.purpose}, {self.account}, {self.price}, {self.processed})'


class DepositEntry(Base):
    __tablename__ = 'deposit'

    _id = Column(Integer, primary_key=True)
    admin = Column(VARCHAR, ForeignKey('user.name'))
    user = Column(VARCHAR, ForeignKey('user.name'))
    amount = Column(Float, nullable=False)
    timestamp = Column(Date, nullable=False)

    def __repr__(self) -> str:
        return f'Deposit({self.user}, {self.amount}, {self.timestamp})'
