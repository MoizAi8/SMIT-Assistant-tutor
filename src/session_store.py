"""Persistent session store backed by JSON file on disk.

Chat sessions survive server restarts. Each session belongs to a user
and stores conversation history, grade context, and metadata.
"""

import json, uuid, threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from src.models import ChatSession, GradingResult

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SESSIONS_FILE = DATA_DIR / "sessions.json"

_lock = threading.Lock()


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_raw() -> dict[str, dict]:
    _ensure_data_dir()
    if not SESSIONS_FILE.exists():
        return {}
    with open(SESSIONS_FILE) as f:
        return json.load(f)


def _save_raw(data: dict[str, dict]):
    _ensure_data_dir()
    with open(SESSIONS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _session_to_dict(s: ChatSession) -> dict:
    return {
        "id": s.id,
        "user_id": s.user_id,
        "title": s.title,
        "history": s.history,
        "max_history": s.max_history,
        "last_grade": s.last_grade.model_dump() if s.last_grade else None,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
    }


def _dict_to_session(d: dict) -> ChatSession:
    grade = None
    if d.get("last_grade"):
        try:
            grade = GradingResult(**d["last_grade"])
        except Exception:
            grade = None
    return ChatSession(
        id=d["id"], user_id=d["user_id"], title=d.get("title", "Untitled"),
        history=d.get("history", []), max_history=d.get("max_history", 20),
        last_grade=grade, created_at=d.get("created_at", ""),
        updated_at=d.get("updated_at", ""),
    )


def create_session(user_id: str, title: str = "") -> ChatSession:
    with _lock:
        sid = str(uuid.uuid4())
        session = ChatSession(
            id=sid, user_id=user_id, title=title or "New Chat",
        )
        raw = _load_raw()
        raw[sid] = _session_to_dict(session)
        _save_raw(raw)
        return session


def get_session(session_id: str) -> ChatSession | None:
    raw = _load_raw()
    d = raw.get(session_id)
    if not d:
        return None
    return _dict_to_session(d)


def get_user_sessions(user_id: str) -> list[ChatSession]:
    raw = _load_raw()
    sessions = []
    for d in raw.values():
        if d.get("user_id") == user_id:
            sessions.append(_dict_to_session(d))
    sessions.sort(key=lambda s: s.updated_at, reverse=True)
    return sessions


def update_session(session: ChatSession):
    with _lock:
        raw = _load_raw()
        raw[session.id] = _session_to_dict(session)
        _save_raw(raw)


def delete_session(session_id: str):
    with _lock:
        raw = _load_raw()
        raw.pop(session_id, None)
        _save_raw(raw)


def add_message(session_id: str, role: str, content: str):
    with _lock:
        raw = _load_raw()
        d = raw.get(session_id)
        if not d:
            return
        session = _dict_to_session(d)
        session.add_message(role, content)
        raw[session_id] = _session_to_dict(session)
        _save_raw(raw)


def update_last_grade(session_id: str, grade: GradingResult):
    with _lock:
        raw = _load_raw()
        d = raw.get(session_id)
        if not d:
            return
        session = _dict_to_session(d)
        session.last_grade = grade
        session.updated_at = datetime.now(timezone.utc).isoformat()
        raw[session_id] = _session_to_dict(session)
        _save_raw(raw)
