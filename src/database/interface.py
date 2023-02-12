from datetime import datetime
from typing import List, Union

from flask_security.utils import verify_password, hash_password
from passlib.context import CryptContext
from sqlalchemy import select, delete

from database.database import SQLDatabase, DatabaseError
from database.database_objects import BunClassEntry, UserEntry, RoleEntry, SingleOrderEntry, OrderEntry, DepositEntry, \
    PurchaseEntry
from database.offline_objects import SecurityUser, Purchase


class MettInterface(SQLDatabase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initialize_bun_classes(self):
        with self.get_read_write_session() as session:
            if not self.list_bun_classes():
                half_buns = get_bun_names(self.config.get('Mett', 'half_buns'))
                if len(half_buns) > 1:
                    raise DatabaseError('Please define only one or none half bun in config')
                normal_buns = get_bun_names(self.config.get('Mett', 'default_buns'))
                if self.config.get('Mett', 'default_spare') not in normal_buns:
                    raise DatabaseError('Please select a default spare from default (not-half) buns')
                for bun in half_buns + normal_buns:
                    bun_entry = BunClassEntry(
                        name=bun.strip(),
                        price=self.config.getfloat('Mett', 'default_price'),
                        mett=self.config.getfloat('Mett', 'default_grams')
                    )
                    session.add(bun_entry)

    def create_user(self, name: str, password: str, is_hashed: bool = False):
        if self.user_exists(name):
            raise DatabaseError('User already exists')
        if not is_hashed and not password_is_legal(password):
            raise DatabaseError('Illegal password. Ask admin for password rules.')
        with self.get_read_write_session() as session:
            new_entry = UserEntry(
                name=name,
                password=password if is_hashed else hash_password(password),
                balance=0.0
            )
            session.add(new_entry)
            return new_entry

    def get_user(self, name) -> Union[SecurityUser, None]:
        with self.get_read_write_session() as session:
            if not self.user_exists(name):
                return None

            user_entry = session.get(UserEntry, name)
            return SecurityUser(name=user_entry.name, password=user_entry.password, roles=[role.name for role in user_entry.roles])

    def get_balance(self, name) -> Union[float, None]:
        return self._get_user_attribute(name, 'balance')

    def _get_user_attribute(self, username: str, attribute: str):
        with self.get_read_write_session() as session:
            if not self.user_exists(username):
                return None

            user = session.get(UserEntry, username)
            return getattr(user, attribute)

    def add_role_to_user(self, user: str, role: str):
        if not self.user_exists(user) or not self.role_exists(role):
            raise DatabaseError('User or role does not exist')
        with self.get_read_write_session() as session:
            user_entry = session.get(UserEntry, user)
            if role in [role.name for role in user_entry.roles]:
                raise DatabaseError('User already has role')
            user_entry.roles.append(session.get(RoleEntry, role))

    def remove_role_from_user(self, user, role):
        if not self.user_exists(user) or not self.role_exists(role):
            raise DatabaseError('User or role does not exist')
        with self.get_read_write_session() as session:
            user_entry = session.get(UserEntry, user)
            if role not in [role.name for role in user_entry.roles]:
                raise DatabaseError('User does not have role')
            user_entry.roles.remove(session.get(RoleEntry, role))

    def create_role(self, name: str):
        with self.get_read_write_session() as session:
            new_entry = RoleEntry(name=name)
            session.add(new_entry)
            return new_entry

    def get_role(self, name):
        with self.get_read_write_session() as session:
            return session.get(RoleEntry, name)

    def get_roles(self, user: str) -> List[str]:
        with self.get_read_write_session() as session:
            user_entry = session.get(UserEntry, user)
            return [role.name for role in user_entry.roles]

    def role_exists(self, name: str) -> bool:
        with self.get_read_write_session() as session:
            return session.get(RoleEntry, name) is not None

    def user_exists(self, name: str) -> bool:
        with self.get_read_write_session() as session:
            return session.get(UserEntry, name) is not None

    def add_bun_class(self, name, price, mett_amount):
        with self.get_read_write_session() as session:
            new_entry = BunClassEntry(name=name, price=price, mett=mett_amount)
            session.add(new_entry)

    def bun_class_exists(self, name):
        with self.get_read_write_session() as session:
            return session.get(BunClassEntry, name) is not None

    def list_bun_classes(self) -> list:
        with self.get_read_write_session() as session:
            classes = session.execute(select(BunClassEntry.name))
            return list(classes.scalars())

    def create_order(self, expiry_date: str):
        with self.get_read_write_session() as session:
            if self._is_expired(expiry_date):
                raise DatabaseError('Please enter date that hasn\'t expired yet')
            if self.active_order_exists():
                raise DatabaseError('No new order can be initialized while another one is active')

            new_entry = OrderEntry(
                expiry_date=datetime.strptime(expiry_date, '%Y-%m-%d').date(),
                processed=False
            )
            session.add(new_entry)
            return new_entry

    def active_order_exists(self):
        with self.get_read_write_session() as session:
            query = select(OrderEntry._id).filter(OrderEntry.processed == False)
            return session.execute(query).first() is not None

    def _is_expired(self, expiry_date):
        expiry_time = self.config.get('DEFAULT', 'expiry_time').strip()
        return datetime.strptime('{} {}'.format(expiry_date, expiry_time), '%Y-%m-%d %H:%M:%S') < datetime.now()

    def current_order_is_expired(self):
        with self.get_read_write_session() as session:
            if not self.active_order_exists():
                raise DatabaseError('There is no active order')
            return self._is_expired(self._get_current_order(session).expiry_date)

    @staticmethod
    def _get_current_order(session) -> OrderEntry:
        return session.execute(select(OrderEntry).where(OrderEntry.processed == False)).one_or_none()[0]

    def drop_current_order(self):
        # drop current order
        with self.get_read_write_session() as session:
            session.execute(delete(OrderEntry).where(OrderEntry.processed == False))

    def order_bun(self, user: str, bun_class: str):
        with self.get_read_write_session() as session:
            order = self._get_current_order(session)
            bun = session.get(BunClassEntry, bun_class)
            user = session.get(UserEntry, user)
            entry = SingleOrderEntry(account=user.name, bun=bun.name, order=order._id)
            session.add(entry)

    def process_order(self):
        # set expire of current order to true and decrease balances according to order
        with self.get_read_write_session() as session:
            order = self._get_current_order(session)
            for bun in order.buns:
                self._charge_bun(session, bun.account, bun.bun)

            order.processed = True

    def _charge_bun(self, session, account, bun):
        price = session.get(BunClassEntry, bun).price
        user = session.get(UserEntry, account)
        user.balance -= price

    def change_balance(self, account, amount, admin):
        # Store which admin has allowed the balance change
        if not self.user_exists(account) or not self.user_exists(admin):
            raise DatabaseError('User does not exist')
        with self.get_read_write_session() as session:
            user = session.get(UserEntry, account)
            user.balance += amount
            deposit = DepositEntry(admin=admin, user=account, amount=amount, timestamp=datetime.now().date())
            session.add(deposit)

    def list_accounts(self):
        with self.get_read_write_session() as session:
            accounts = session.scalars(select(UserEntry).order_by(UserEntry.name)).all()
            return [account.name for account in accounts]

    def state_purchase(self, account, amount, purpose):
        # add account, amount, purpose as non-processed purchase
        with self.get_read_write_session() as session:
            entry = PurchaseEntry(
                account=account,
                price=amount,
                purpose=purpose,
                timestamp=datetime.now().date(),
                processed=False
            )
            session.add(entry)

    def list_purchases(self, processed: bool = False):
        # list purchases, if processed is false only those that have not been authorized or declined
        with self.get_read_write_session() as session:
            purchases = session.scalars(select(PurchaseEntry).where(PurchaseEntry.processed == processed)).all()
            return [
                Purchase(
                    p_id=purchase._id,
                    account=purchase.account,
                    price=purchase.price,
                    purpose=purchase.purpose,
                    timestamp=purchase.timestamp,
                    processed={
                        'authorized': purchase.authorized,
                        'by': purchase.by,
                        'at': purchase.at
                    }
                )
                for purchase in purchases
            ]

    def authorize_purchase(self, purchase_id, admin):
        # add purchase.amount to purchase.account.balance
        if not self.user_exists(admin):
            raise DatabaseError('Admin name does not exist')
        with self.get_read_write_session() as session:
            entry = session.get(PurchaseEntry, purchase_id)

            if entry.processed:
                raise DatabaseError('Purchase already processed')

            entry.processed = True
            entry.authorized = True
            entry.at = datetime.now().date()
            entry.by = admin

            self.change_balance(entry.account, entry.price, admin)

    def decline_purchase(self, purchase_id, admin):
        # drop purchase
        if not self.user_exists(admin):
            raise DatabaseError('Admin name does not exist')
        with self.get_read_write_session() as session:
            entry = session.get(PurchaseEntry, purchase_id)

            if entry.processed:
                raise DatabaseError('Purchase already processed')

            entry.processed = True
            entry.authorized = False
            entry.at = datetime.now().date()
            entry.by = admin

    def list_roles(self):
        with self.get_read_write_session() as session:
            roles = session.scalars(select(RoleEntry).order_by(RoleEntry.name)).all()
            return [role.name for role in roles]

    def password_is_correct(self, user_name, password):
        stored_password = self.get_user(user_name).password
        return verify_password(password, stored_password)

    def change_password(self, user_name, password):
        if not self.user_exists(user_name):
            raise DatabaseError('User does not exist')
        if not password_is_legal(password):
            raise DatabaseError('Illegal password. Ask admin for password rules.')
        with self.get_read_write_session() as session:
            entry = session.get(UserEntry, user_name)
            entry.password = hash_password(password)

    def find_user(self, id):
        return self.get_user(id)

    def find_role(self, role):
        raise NotImplementedError()  # Will stay un-implemented. flask-security artifact

    def toggle_active(self, user):
        raise NotImplementedError()  # Will stay un-implemented. flask-security artifact

    def deactivate_user(self, user):
        raise NotImplementedError()  # Will stay un-implemented. flask-security artifact

    def activate_user(self, user):
        raise NotImplementedError()  # Will stay un-implemented. flask-security artifact

    def find_or_create_role(self, name, **kwargs):
        raise NotImplementedError()  # Will stay un-implemented. flask-security artifact

    def delete_user(self, user: str):
        if not self.user_exists(user):
            raise DatabaseError('User does not exist')
        with self.get_read_write_session() as session:
            session.execute(delete(UserEntry).where(UserEntry.name == user))

    def commit(self):
        pass  # Will stay un-implemented. flask-security artifact

    def get_deposits(self):
        with self.get_read_write_session() as session:
            deposits = session.scalars(select(DepositEntry)).all()
            return [
                {
                    'amount': deposit.amount,
                    'user': deposit.user,
                    'admin': deposit.admin,
                    'timestamp': deposit.timestamp
                } for deposit in deposits
            ]

    def change_mett_formula(self, bun: str, amount: float):
        # set mett amount for referenced bun
        if not self.bun_class_exists(bun):
            raise DatabaseError('Bun class does not exist')
        with self.get_read_write_session() as session:
            entry = session.get(BunClassEntry, bun)
            entry.mett = amount

    def change_bun_price(self, bun, price):
        # set mett price for referenced bun
        if not self.bun_class_exists(bun):
            raise DatabaseError('Bun class does not exist')
        with self.get_read_write_session() as session:
            entry = session.get(BunClassEntry, bun)
            entry.price = price

    def assign_spare(self, bun_class, user):
        with self.get_read_write_session() as session:
            self._charge_bun(session=session, account=user, bun=bun_class)

    def reroute_bun(self, bun_class, user, target):
        # Change order from one user to another
        user_buns = self.get_current_user_buns(user)
        if user_buns[bun_class] == 0:
            raise DatabaseError(f'No {bun_class} bun order by {user}')
        with self.get_read_write_session() as session:
            single_order = self._find_single_order(user, bun_class, session)
            single_order.account = target

    def _find_single_order(self, user, bun, session) -> SingleOrderEntry:
        current_order = self._get_current_order(session)
        for single_order in current_order.buns:
            if single_order.bun == bun and single_order.account == user:
                return single_order
        raise DatabaseError('Could not find bun to re-route')

    def get_order_history(self, user):
        # TODO Please refactor
        # get average per bun and average total of a user's orders (that she / he participated in)
        with self.get_read_write_session() as session:
            orders = session.scalars(select(OrderEntry).where(OrderEntry.processed == True)).all()
            user_has_ordered, flag = 0, False
            order = {bun_class: 0 for bun_class in self.list_bun_classes()}
            for former_order in orders:
                for ordered_bun in former_order.buns:
                    if ordered_bun.account == user:
                        order[ordered_bun.bun] += 1
                        flag = True
                if flag:
                    user_has_ordered += 1
                    flag = False
            if user_has_ordered > 0:
                for bun_class in order:
                    order[bun_class] = order[bun_class] / user_has_ordered
            mean_over_all = sum(order[bun] for bun in order)
            return order, mean_over_all

    def get_current_user_buns(self, user):
        # get list of buns ordered by user
        if not self.user_exists(user):
            raise DatabaseError('User does not exist')
        return self._get_bun_order(lambda x: x == user)

    def get_current_bun_order(self, include_spares: bool = True):
        # get aggregated current bun order
        current_bun_order = self._get_bun_order(lambda _: True)
        return self._add_spares(current_bun_order) if include_spares else current_bun_order

    def _add_spares(self, current_bun_order):
        half_buns = get_bun_names(self.config.get('Mett', 'half_buns'))
        spare_count = self.config.getint('Mett', 'spare_count')
        if half_buns and (current_bun_order[half_buns[0]] % 2) == 1:
            current_bun_order[half_buns[0]] += 1
            current_bun_order[self.config.get('Mett', 'default_spare')] += spare_count - 1 if spare_count > 0 else 0
            return current_bun_order
        current_bun_order[self.config.get('Mett', 'default_spare')] += spare_count
        return current_bun_order

    def _get_bun_order(self, user_filter) -> dict:
        if not self.active_order_exists():
            raise DatabaseError('No active order')
        with self.get_read_write_session() as session:
            bun_order = {bun_class: 0 for bun_class in self.list_bun_classes()}
            order = self._get_current_order(session)
            for bun in order.buns:
                if user_filter(bun.account):
                    bun_order[bun.bun] += 1
        return bun_order

    def get_current_mett_order(self, include_spares: bool = True) -> float:
        # generate mett order from bun order
        if not self.active_order_exists():
            raise DatabaseError('No active order')
        ordered_buns = self.get_current_bun_order(include_spares=include_spares)
        with self.get_read_write_session() as session:
            return sum(
                bun.mett * count for bun, count in [
                    (session.get(BunClassEntry, name), count) for name, count in ordered_buns.items()]
            )

    def list_bun_classes_with_price(self) -> dict:
        with self.get_read_write_session() as session:
            return {bun.name: bun.price for bun in session.scalars(select(BunClassEntry)).all()}

    def list_bun_classes_with_mett(self) -> dict:
        with self.get_read_write_session() as session:
            return {bun.name: bun.mett for bun in session.scalars(select(BunClassEntry)).all()}

    def get_all_order_information(self) -> list:
        with self.get_read_write_session() as session:
            return [
                {'_id': order._id, 'orders': [(bun.account, bun.bun) for bun in order.buns]}
                for order in session.scalars(select(OrderEntry)).all()
            ]


def password_is_legal(password: str) -> bool:
    if not password:
        return False
    schemes = ['bcrypt', 'des_crypt', 'pbkdf2_sha256', 'pbkdf2_sha512', 'sha256_crypt', 'sha512_crypt', 'plaintext']
    ctx = CryptContext(schemes=schemes)
    return ctx.identify(password) == 'plaintext'


def get_bun_names(csv_string: str) -> List[str]:
    return [s for s in csv_string.split(',') if s]
