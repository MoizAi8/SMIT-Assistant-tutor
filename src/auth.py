"""JWT authentication, password hashing, and role-based access control.

Default users (created on first run):
  admin / admin123   — full access, manage users
  teacher / teacher123 — grade submissions, view analytics
  student / student123 — submit assignments, chat with TA

Users are stored in data/users.json
"""

import json, hashlib, hmac, base64, os, time, secrets
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Any

import jwt as pyjwt

from src.models import User, ROLES

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "smit-ta-secret-key-change-in-production")


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}:{pwd_hash}"


def _verify_password(password: str, stored: str) -> bool:
    salt, pwd_hash = stored.split(":", 1)
    return hmac.compare_digest(
        hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex(),
        pwd_hash,
    )


def _load_users() -> dict[str, User]:
    _ensure_data_dir()
    if not USERS_FILE.exists():
        return _seed_default_users()
    with open(USERS_FILE) as f:
        raw = json.load(f)
    return {uid: User(**data) for uid, data in raw.items()}


def _save_users(users: dict[str, User]):
    _ensure_data_dir()
    raw = {uid: {
        "id": u.id, "username": u.username, "password_hash": u.password_hash,
        "role": u.role, "display_name": u.display_name, "created_at": u.created_at,
    } for uid, u in users.items()}
    with open(USERS_FILE, "w") as f:
        json.dump(raw, f, indent=2)


def _seed_default_users() -> dict[str, User]:
    defaults = [
        User(id="user_admin", username="admin", password_hash=_hash_password("admin123"),
             role="admin", display_name="Administrator"),
        User(id="user_teacher", username="teacher", password_hash=_hash_password("teacher123"),
             role="teacher", display_name="Sir Ahmed"),
        User(id="user_student", username="student", password_hash=_hash_password("student123"),
             role="student", display_name="Ali"),
    ]
    users = {u.id: u for u in defaults}
    _save_users(users)
    return users


def create_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400,
    }
    return pyjwt.encode(payload, SECRET_KEY, algorithm="HS256")


def verify_token(token: str) -> dict[str, Any] | None:
    try:
        return pyjwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except Exception:
        return None


def authenticate(username: str, password: str) -> tuple[str, User] | None:
    users = _load_users()
    for u in users.values():
        if u.username == username and _verify_password(password, u.password_hash):
            token = create_token(u.id, u.role)
            return token, u
    return None


def register_user(username: str, password: str, role: str = "student",
                  display_name: str = "") -> tuple[str, User] | None:
    if role not in ROLES:
        return None
    users = _load_users()
    if any(u.username == username for u in users.values()):
        return None
    uid = f"user_{username}_{secrets.token_hex(4)}"
    user = User(
        id=uid, username=username, password_hash=_hash_password(password),
        role=role, display_name=display_name or username,
    )
    users[uid] = user
    _save_users(users)
    token = create_token(uid, role)
    return token, user


def get_user_by_id(user_id: str) -> User | None:
    users = _load_users()
    return users.get(user_id)


def get_user_from_token(token: str) -> User | None:
    payload = verify_token(token)
    if not payload:
        return None
    return get_user_by_id(payload["sub"])


def require_role(allowed_roles: list[str]):
    """Decorator factory — usage: @require_role(['admin','teacher'])"""
    def decorator(func):
        func._required_roles = allowed_roles
        return func
    return decorator


def has_required_role(user: User, endpoint) -> bool:
    roles = getattr(endpoint, "_required_roles", None)
    if roles is None:
        return True
    return user.role in roles
