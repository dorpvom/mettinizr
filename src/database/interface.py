from database.objects import BunClassEntry, UserEntry, RoleEntry, SingleOrderEntry, OrderEntry, DepositEntry, PurchaseEntry, PurchaseAuthorizationEntry
from database.database import SQLDatabase


class MettInterface(SQLDatabase):
    def add_user(self, name: str, password: str):
        with self.get_read_write_session() as session:
            new_entry = UserEntry(name=name, password=password)
            session.add(new_entry)

    def user_exists(self, name: str) -> bool:
        with self.get_read_write_session() as session:
            return session.get(UserEntry, name) is not None
