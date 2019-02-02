from flask_security import SQLAlchemyUserDatastore
from flask_security.utils import verify_password, hash_password
from passlib.context import CryptContext


class UserRoleDatabase(SQLAlchemyUserDatastore):
    def list_users(self):
        user_list = self.user_model.query.all()
        return user_list

    def list_roles(self):
        role_list = self.role_model.query.all()
        return role_list

    def password_is_correct(self, user_name, password):
        user = self.find_user(email=user_name)
        return verify_password(password, user.password)

    def change_password(self, user_name, password):
        user = self.find_user(email=user_name)
        user.password = hash_password(password)
        self.put(user)

    def user_exists(self, user_name):
        user = self.find_user(email=user_name)
        return bool(user)

    def role_exists(self, role):
        role = self.find_role(role)
        return bool(role)


def password_is_legal(password: str) -> bool:
    if not password:
        return False
    schemes = ['bcrypt', 'des_crypt', 'pbkdf2_sha256', 'pbkdf2_sha512', 'sha256_crypt', 'sha512_crypt', 'plaintext']
    ctx = CryptContext(schemes=schemes)
    return ctx.identify(password) == 'plaintext'
