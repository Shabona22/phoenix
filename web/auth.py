"""Panel authentication helpers."""

from __future__ import annotations

import os

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

DEFAULT_USER = os.environ.get("PHOENIX_PANEL_USER", "admin")
DEFAULT_PASS = os.environ.get("PHOENIX_PANEL_PASSWORD", "phoenix123")


class PanelUser(UserMixin):
    def __init__(self, user_id: int, username: str, password_hash: str):
        self.id = str(user_id)
        self.username = username
        self.password_hash = password_hash


def build_users() -> dict[str, PanelUser]:
    return {
        DEFAULT_USER: PanelUser(
            1,
            DEFAULT_USER,
            generate_password_hash(os.environ.get("PHOENIX_PANEL_PASSWORD_HASH") or DEFAULT_PASS),
        )
    }


def verify_user(users: dict[str, PanelUser], username: str, password: str) -> PanelUser | None:
    user = users.get(username)
    if user and check_password_hash(user.password_hash, password):
        return user
    return None
