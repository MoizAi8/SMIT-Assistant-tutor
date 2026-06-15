"""Shared fixtures for the SMIT Teaching Assistant test suite."""

import os, json, tempfile, uuid, pytest, asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

# ─── Force DEMO mode ─────────────────────────────────────────────
os.environ["OPENAI_API_KEY"] = ""  # no live AI calls during tests


# ─── Teach context factory ────────────────────────────────────────

@pytest.fixture
def make_context():
    """Return a factory for TeachingContext."""
    def _make(**overrides):
        from src.models import TeachingContext
        defaults = dict(
            assignment_title="Temperature Converter",
            assignment_instructions="Create a program that converts temperatures between Celsius and Fahrenheit. Use functions, handle invalid input.",
            rubric="Function definitions (30 points): define celsius_to_fahrenheit and fahrenheit_to_celsius. Input handling (20 points): convert input to float. Output (20 points): clear formatted output. Error handling (15 points): try-except. Code quality (15 points): docstrings, naming, formatting.",
            total_marks=100,
            student_code="def celsius_to_fahrenheit(c):\n    return (c * 9/5) + 32\n\ndef fahrenheit_to_celsius(f):\n    return (f - 32) * 5/9\n\ndef main():\n    temp = float(input(\"Enter temp: \"))\n    scale = input(\"C/F? \")\n    if scale.upper() == 'C':\n        result = celsius_to_fahrenheit(temp)\n        print(f\"{temp}C = {result}F\")\n    else:\n        result = fahrenheit_to_celsius(temp)\n        print(f\"{temp}F = {result}C\")\n\nif __name__ == '__main__':\n    main()",
            file_name="temp_converter.py",
            folder_structure="",
            expected_output="",
            sample_output="Enter temp: 100\nC/F? C\n100C = 212F",
            previous_feedback="",
            class_notes="",
            common_mistakes="",
            student_name="Ali",
        )
        defaults.update(overrides)
        return TeachingContext(**defaults)
    return _make


# ─── Grade result factory ────────────────────────────────────────

@pytest.fixture
def make_grade():
    """Return a factory for GradingResult."""
    def _make(**overrides):
        from src.models import GradingResult
        defaults = dict(
            score="85/100",
            verdict="Good effort! Aap ne accha code likha hai.",
            what_went_well=["Functions are well-structured", "Proper use of conversion formulas"],
            major_issues=["Missing error handling for invalid input"],
            explanation="Good work overall, but needs try-except.",
            suggested_improvements=["Add try-except around input()"],
            corrected_code="# Corrected code\n\ndef celsius_to_fahrenheit(c):\n    return (c * 9/5) + 32",
        )
        defaults.update(overrides)
        return GradingResult(**defaults)
    return _make


# ─── Session factory ─────────────────────────────────────────────

def make_session(**overrides: Any) -> Any:
    from src.models import ChatSession
    now = datetime.now(timezone.utc).isoformat()
    defaults = dict(
        id=str(uuid.uuid4()),
        user_id="test_user",
        title="Test Chat",
        history=[],
        max_history=20,
        last_grade=None,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return ChatSession(**defaults)


# ─── Temp dir for data files ─────────────────────────────────────

@pytest.fixture
def tmp_data_dir(monkeypatch: pytest.MonkeyPatch) -> Path:
    """Replace DATA_DIR and computed file paths with a temp dir."""
    tmp = Path(tempfile.mkdtemp())
    import src.auth as auth_mod
    import src.session_store as store_mod
    monkeypatch.setattr(auth_mod, "DATA_DIR", tmp)
    monkeypatch.setattr(auth_mod, "USERS_FILE", tmp / "users.json")
    monkeypatch.setattr(store_mod, "DATA_DIR", tmp)
    monkeypatch.setattr(store_mod, "SESSIONS_FILE", tmp / "sessions.json")
    return tmp


@pytest.fixture
def seed_users(tmp_data_dir: Path) -> dict:
    """Seed default test users into a temp data dir."""
    from src.auth import _seed_default_users
    return _seed_default_users()


@pytest.fixture
def http_client(tmp_data_dir: Path):
    """Return an AsyncClient for API testing with clean data dir."""
    from httpx import AsyncClient, ASGITransport
    from api.main import app
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    return client


@pytest.fixture
def auth_token(tmp_data_dir: Path) -> str:
    """Return a valid JWT token for the default admin user."""
    from src.auth import authenticate
    result = authenticate("admin", "admin123")
    assert result is not None
    token, _ = result
    return token


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}
