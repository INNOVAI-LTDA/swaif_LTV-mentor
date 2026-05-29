from app.storage.user_repository import UserRepository
from app.core.security import hash_password

def get_all_users():
    repo = UserRepository()
    return repo.list_users()


def create_user(payload: dict):
    repo = UserRepository()
    email = payload.get("email")
    password = payload.get("password", "user123")  # default password if not provided
    role = payload.get("role", "user")
    is_active = payload.get("is_active", True)
    password_hash = hash_password(password)
    return repo.create(email=email, password_hash=password_hash, role=role, is_active=is_active)
