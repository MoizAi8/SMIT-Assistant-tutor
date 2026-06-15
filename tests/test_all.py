"""100+ comprehensive tests covering every module in the SMIT Teaching Assistant."""

import pytest, asyncio
from datetime import datetime, timezone
from typing import Any

# ─── Helper: call a @function_tool with a TeachingContext ─────────────────

async def run_tool(tool, context, json_args: str = "{}"):
    """Invoke a `@function_tool` decorated function with a TeachingContext."""
    from agents.tool import ToolContext
    impl = tool.on_invoke_tool._invoke_tool_impl
    tc = ToolContext(
        context=context,
        tool_name=tool.name,
        tool_call_id="test_call",
        tool_arguments=json_args,
    )
    return await impl(tc, json_args)


# ===================================================================
# 1. config.py
# ===================================================================


class TestConfig:
    def test_model_default(self):
        from src.config import OPENAI_MODEL
        assert OPENAI_MODEL

    def test_api_key_settable(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        import importlib
        from src import config
        importlib.reload(config)
        from src.config import OPENAI_API_KEY
        assert OPENAI_API_KEY == "sk-test"

    def test_require_api_key_raises(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "")
        import importlib
        from src import config
        importlib.reload(config)
        from src.config import require_api_key
        with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
            require_api_key()

    def test_base_url_default(self):
        from src.config import OPENAI_BASE_URL
        assert isinstance(OPENAI_BASE_URL, str)

# ===================================================================
# 2. models.py
# ===================================================================


class TestModels:
    def test_chat_session_defaults(self):
        from src.models import ChatSession
        s = ChatSession(id="s1", user_id="u1", title="Chat")
        assert s.id == "s1"
        assert s.user_id == "u1"
        assert s.history == []
        assert s.max_history == 20
        assert s.last_grade is None
        assert s.created_at != ""
        assert s.updated_at != ""

    def test_chat_session_add_message(self):
        from src.models import ChatSession
        s = ChatSession(id="s1", user_id="u1", title="Chat")
        s.add_message("user", "Hello")
        assert len(s.history) == 1
        assert s.history[0] == {"role": "user", "content": "Hello"}

    def test_chat_session_add_message_overflow(self):
        from src.models import ChatSession
        s = ChatSession(id="s1", user_id="u1", title="Chat", max_history=2)
        for i in range(10):
            s.add_message("user", f"msg{i}")
        assert len(s.history) <= 4

    def test_get_context_window(self):
        from src.models import ChatSession
        s = ChatSession(id="s1", user_id="u1", title="Chat", max_history=3)
        for i in range(10):
            s.add_message("user", f"msg{i}")
        ctx = s.get_context_window()
        assert len(ctx) <= 6

    def test_to_dict_last_grade_none(self):
        from src.models import ChatSession
        s = ChatSession(id="s1", user_id="u1", title="Chat")
        d = s.to_dict()
        assert d["last_grade"] is None
        assert "history" in d

    def test_to_dict_last_grade_present(self):
        from src.models import ChatSession, GradingResult
        g = GradingResult(score="90/100", verdict="Good", what_went_well=[], major_issues=[], explanation="Ok", suggested_improvements=[], corrected_code="")
        s = ChatSession(id="s1", user_id="u1", title="Chat", last_grade=g)
        d = s.to_dict()
        assert d["last_grade"]["score"] == "90/100"

    def test_user_defaults(self):
        from src.models import User
        u = User(id="u1", username="test", password_hash="abc", role="student")
        assert u.display_name == "test"
        assert u.created_at != ""

    def test_user_with_display_name(self):
        from src.models import User
        u = User(id="u1", username="test", password_hash="abc", role="teacher", display_name="Sir")
        assert u.display_name == "Sir"

    def test_roles_constant(self):
        from src.models import ROLES
        assert "admin" in ROLES
        assert "teacher" in ROLES
        assert "student" in ROLES
        assert len(ROLES) == 3

    def test_grading_result_validation(self):
        from src.models import GradingResult
        g = GradingResult(score="75/100", verdict="Good", what_went_well=[], major_issues=[], explanation="Nice", suggested_improvements=[], corrected_code="code")
        assert g.score == "75/100"
        assert g.model_dump()["score"] == "75/100"

# ===================================================================
# 3. context_windows.py
# ===================================================================


class TestContextWindows:
    def test_creation(self):
        from src.context_windows import ContextWindows
        cw = ContextWindows()
        assert cw.W1_assignment == {}
        assert cw.W2_code == {}
        assert cw.W7_session == {}

    def test_from_teaching_context(self, make_context):
        from src.context_windows import ContextWindows
        ctx = make_context()
        cw = ContextWindows.from_teaching_context(ctx)
        assert cw.W1_assignment["title"] == "Temperature Converter"
        assert "code" in cw.W2_code
        assert cw.W3_rubric["rubric_text"] != ""
        assert cw.W4_output["sample"] != ""
        assert cw.W7_session["student_name"] == "Ali"

    def test_render_for_prompt_contains_windows(self, make_context):
        from src.context_windows import ContextWindows
        cw = ContextWindows.from_teaching_context(make_context())
        text = cw.render_for_prompt()
        assert all(f"[{w}]" in text for w in ["W1","W2","W3","W4","W5","W6","W7"])

    def test_render_for_prompt_empty_windows(self):
        from src.context_windows import ContextWindows
        cw = ContextWindows()
        text = cw.render_for_prompt()
        assert "(empty)" in text

    def test_get_window_known(self, make_context):
        from src.context_windows import ContextWindows
        cw = ContextWindows.from_teaching_context(make_context())
        assert cw.get_window("W1")["title"] == "Temperature Converter"
        assert "code" in cw.get_window("W2")
        assert cw.get_window("W3")["rubric_text"] != ""

    def test_get_window_unknown(self):
        from src.context_windows import ContextWindows
        assert ContextWindows().get_window("W99") == {}

    def test_get_window_case_insensitive(self, make_context):
        from src.context_windows import ContextWindows
        cw = ContextWindows.from_teaching_context(make_context())
        assert cw.get_window("w1")["title"] == "Temperature Converter"

    def test_window_specs_keys(self):
        from src.context_windows import WINDOW_SPECS
        assert list(WINDOW_SPECS.keys()) == ["W1", "W2", "W3", "W4", "W5", "W6", "W7"]

    def test_from_teaching_context_empty(self):
        from src.context_windows import ContextWindows
        from src.models import TeachingContext
        cw = ContextWindows.from_teaching_context(TeachingContext())
        assert cw.W1_assignment["title"] == ""
        assert cw.W7_session["student_name"] == "Student"

    def test_render_truncates_long_values(self, make_context):
        from src.context_windows import ContextWindows
        ctx = make_context(student_code="a" * 500)
        cw = ContextWindows.from_teaching_context(ctx)
        text = cw.render_for_prompt()
        assert "a" * 200 in text
        assert "a" * 201 not in text

# ===================================================================
# 4. knowledge_base.py
# ===================================================================


class TestKnowledgeBase:
    def test_hints_for_python(self):
        from src.knowledge_base import get_hints_for_code
        hints = get_hints_for_code("def foo():\n    pass")
        assert len(hints) >= 1

    def test_hints_for_input_without_conversion(self):
        from src.knowledge_base import get_hints_for_code
        hints = get_hints_for_code("x = input('enter: ')")
        assert any("int()" in h or "float()" in h for h in hints)

    def test_hints_for_empty_code(self):
        from src.knowledge_base import get_hints_for_code
        assert get_hints_for_code("") == []

    def test_notes_for_functions(self):
        from src.knowledge_base import get_notes_for_code
        notes = get_notes_for_code("def foo():\n    return 1")
        assert len(notes) >= 1

    def test_notes_for_conditionals(self):
        from src.knowledge_base import get_notes_for_code
        notes = get_notes_for_code("if x > 0:\n    print('positive')")
        assert any("if" in n.lower() for n in notes)

    def test_notes_for_loops(self):
        from src.knowledge_base import get_notes_for_code
        notes = get_notes_for_code("for i in range(10):\n    print(i)")
        assert len(notes) >= 1

# ===================================================================
# 5. auth.py
# ===================================================================


class TestAuth:
    def test_hash_password_format(self, tmp_data_dir):
        from src.auth import _hash_password
        hashed = _hash_password("test123")
        assert ":" in hashed
        salt, pwd = hashed.split(":", 1)
        assert len(salt) == 32
        assert len(pwd) == 64

    def test_verify_password_correct(self, tmp_data_dir):
        from src.auth import _hash_password, _verify_password
        hashed = _hash_password("test123")
        assert _verify_password("test123", hashed)

    def test_verify_password_wrong(self, tmp_data_dir):
        from src.auth import _hash_password, _verify_password
        hashed = _hash_password("test123")
        assert not _verify_password("wrong", hashed)

    def test_authenticate_valid(self, tmp_data_dir, seed_users):
        from src.auth import authenticate
        result = authenticate("admin", "admin123")
        assert result is not None
        token, user = result
        assert user.username == "admin"
        assert user.role == "admin"
        assert isinstance(token, str) and len(token) > 20

    def test_authenticate_invalid(self, tmp_data_dir, seed_users):
        from src.auth import authenticate
        assert authenticate("admin", "wrongpass") is None
        assert authenticate("nonexistent", "pass") is None

    def test_register_user_creates(self, tmp_data_dir):
        from src.auth import register_user
        result = register_user("newuser", "pass123", "student", "New User")
        assert result is not None
        token, user = result
        assert user.username == "newuser"
        assert user.display_name == "New User"

    def test_register_user_duplicate(self, tmp_data_dir, seed_users):
        from src.auth import register_user
        assert register_user("admin", "pass123", "student") is None

    def test_register_user_invalid_role(self, tmp_data_dir):
        from src.auth import register_user
        assert register_user("x", "pass", "superadmin") is None

    def test_create_token(self, tmp_data_dir):
        from src.auth import create_token
        token = create_token("user_test", "student")
        assert isinstance(token, str) and len(token) > 20

    def test_verify_token_valid(self, tmp_data_dir):
        from src.auth import create_token, verify_token
        token = create_token("user_test", "student")
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user_test"
        assert payload["role"] == "student"

    def test_verify_token_invalid(self, tmp_data_dir):
        from src.auth import verify_token
        assert verify_token("invalid.token.here") is None

    def test_get_user_from_token_valid(self, tmp_data_dir, seed_users):
        from src.auth import create_token, get_user_from_token
        token = create_token("user_admin", "admin")
        user = get_user_from_token(token)
        assert user is not None
        assert user.username == "admin"

    def test_get_user_from_token_invalid(self, tmp_data_dir):
        from src.auth import get_user_from_token
        assert get_user_from_token("bad.token") is None

    def test_require_role(self):
        from src.auth import require_role
        @require_role(["admin", "teacher"])
        def my_endpoint():
            pass
        assert my_endpoint._required_roles == ["admin", "teacher"]

    def test_has_required_role(self):
        from src.auth import require_role, has_required_role
        from src.models import User
        admin = User(id="a", username="a", password_hash="x", role="admin")
        teacher = User(id="t", username="t", password_hash="x", role="teacher")
        student = User(id="s", username="s", password_hash="x", role="student")
        @require_role(["admin", "teacher"])
        def protected(): pass
        assert has_required_role(admin, protected)
        assert has_required_role(teacher, protected)
        assert not has_required_role(student, protected)

# ===================================================================
# 6. session_store.py
# ===================================================================


class TestSessionStore:
    def test_create_session(self, tmp_data_dir):
        from src import session_store as store
        s = store.create_session("user1", "My Chat")
        assert s.id is not None
        assert s.user_id == "user1"
        assert s.title == "My Chat"

    def test_create_session_default_title(self, tmp_data_dir):
        from src import session_store as store
        s = store.create_session("user1")
        assert s.title == "New Chat"

    def test_get_session_found(self, tmp_data_dir):
        from src import session_store as store
        created = store.create_session("user1", "Test")
        fetched = store.get_session(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.title == "Test"

    def test_get_session_not_found(self, tmp_data_dir):
        from src import session_store as store
        assert store.get_session("nonexistent") is None

    def test_get_user_sessions(self, tmp_data_dir):
        from src import session_store as store
        store.create_session("user_a", "Chat A")
        store.create_session("user_a", "Chat B")
        store.create_session("user_b", "Other")
        user_a_sessions = store.get_user_sessions("user_a")
        assert len(user_a_sessions) == 2
        assert all(s.user_id == "user_a" for s in user_a_sessions)

    def test_get_user_sessions_sorted(self, tmp_data_dir):
        from src import session_store as store
        store.create_session("user_a", "Older")
        store.create_session("user_a", "Newer")
        sessions = store.get_user_sessions("user_a")
        assert sessions[0].title == "Newer"

    def test_update_session(self, tmp_data_dir):
        from src import session_store as store
        s = store.create_session("user1", "Original")
        s.title = "Updated"
        store.update_session(s)
        fetched = store.get_session(s.id)
        assert fetched.title == "Updated"

    def test_delete_session(self, tmp_data_dir):
        from src import session_store as store
        s = store.create_session("user1", "Delete Me")
        store.delete_session(s.id)
        assert store.get_session(s.id) is None

    def test_delete_session_nonexistent(self, tmp_data_dir):
        from src import session_store as store
        store.delete_session("nonexistent")

    def test_add_message(self, tmp_data_dir):
        from src import session_store as store
        s = store.create_session("user1")
        store.add_message(s.id, "user", "Hello")
        fetched = store.get_session(s.id)
        assert len(fetched.history) == 1
        assert fetched.history[0]["content"] == "Hello"

    def test_add_message_nonexistent(self, tmp_data_dir):
        from src import session_store as store
        store.add_message("no-session", "user", "msg")

    def test_update_last_grade(self, tmp_data_dir, make_grade):
        from src import session_store as store
        s = store.create_session("user1")
        grade = make_grade(score="90/100")
        store.update_last_grade(s.id, grade)
        fetched = store.get_session(s.id)
        assert fetched.last_grade is not None
        assert fetched.last_grade.score == "90/100"

    def test_update_last_grade_nonexistent(self, tmp_data_dir, make_grade):
        from src import session_store as store
        store.update_last_grade("no-session", make_grade())

    def test_session_to_dict_roundtrip(self, tmp_data_dir):
        from src import session_store as store
        from src.models import GradingResult
        s = store.create_session("user1")
        grade = GradingResult(score="80/100", verdict="OK", what_went_well=["a"], major_issues=["b"], explanation="c", suggested_improvements=["d"], corrected_code="e")
        store.update_last_grade(s.id, grade)
        fetched = store.get_session(s.id)
        assert fetched.last_grade.score == "80/100"

    def test_empty_user_sessions(self, tmp_data_dir):
        from src import session_store as store
        assert store.get_user_sessions("nobody") == []

# ===================================================================
# 7. guardrails.py
# ===================================================================


@pytest.mark.asyncio
class TestGuardrails:
    @pytest.fixture
    def ctx(self, make_context):
        from agents import RunContextWrapper
        return RunContextWrapper(context=make_context())

    @pytest.fixture
    def empty_ctx(self):
        from agents import RunContextWrapper
        from src.models import TeachingContext
        return RunContextWrapper(context=TeachingContext())

    async def test_input_code_empty(self, empty_ctx):
        from src.guardrails import guardrail_code_not_empty
        result = await guardrail_code_not_empty(empty_ctx, None, "dummy")
        assert result.tripwire_triggered

    async def test_input_code_too_short(self):
        from agents import RunContextWrapper
        from src.models import TeachingContext
        ctx = RunContextWrapper(context=TeachingContext(student_code="short"))
        from src.guardrails import guardrail_code_not_empty
        result = await guardrail_code_not_empty(ctx, None, "dummy")
        assert result.tripwire_triggered

    async def test_input_code_valid(self, ctx):
        from src.guardrails import guardrail_code_not_empty
        result = await guardrail_code_not_empty(ctx, None, "dummy")
        assert not result.tripwire_triggered

    async def test_rubric_empty(self, empty_ctx):
        from src.guardrails import guardrail_rubric_valid
        result = await guardrail_rubric_valid(empty_ctx, None, "")
        assert result.tripwire_triggered

    async def test_rubric_no_numbers(self):
        from agents import RunContextWrapper
        from src.models import TeachingContext
        ctx = RunContextWrapper(context=TeachingContext(rubric="Write good code"))
        from src.guardrails import guardrail_rubric_valid
        result = await guardrail_rubric_valid(ctx, None, "")
        assert result.tripwire_triggered

    async def test_rubric_valid(self, ctx):
        from src.guardrails import guardrail_rubric_valid
        result = await guardrail_rubric_valid(ctx, None, "")
        assert not result.tripwire_triggered

    async def test_instructions_empty(self, empty_ctx):
        from src.guardrails import guardrail_instructions_provided
        result = await guardrail_instructions_provided(empty_ctx, None, "")
        assert result.tripwire_triggered

    async def test_instructions_too_short(self):
        from agents import RunContextWrapper
        from src.models import TeachingContext
        ctx = RunContextWrapper(context=TeachingContext(assignment_instructions="Short"))
        from src.guardrails import guardrail_instructions_provided
        result = await guardrail_instructions_provided(ctx, None, "")
        assert result.tripwire_triggered

    async def test_instructions_valid(self, ctx):
        from src.guardrails import guardrail_instructions_provided
        result = await guardrail_instructions_provided(ctx, None, "")
        assert not result.tripwire_triggered

    async def test_score_anchored_valid(self, ctx, make_grade):
        from src.guardrails import guardrail_score_rubric_anchored
        grade = make_grade(score="85/100")
        result = await guardrail_score_rubric_anchored(ctx, None, grade)
        assert not result.tripwire_triggered

    async def test_score_anchored_wrong_denominator(self, ctx, make_grade):
        from src.guardrails import guardrail_score_rubric_anchored
        grade = make_grade(score="50/50")
        result = await guardrail_score_rubric_anchored(ctx, None, grade)
        assert result.tripwire_triggered

    async def test_score_anchored_exceeds_total(self, ctx, make_grade):
        from src.guardrails import guardrail_score_rubric_anchored
        grade = make_grade(score="200/100")
        result = await guardrail_score_rubric_anchored(ctx, None, grade)
        assert result.tripwire_triggered

    async def test_full_marks_with_issues_triggered(self, ctx, make_grade):
        from src.guardrails import guardrail_no_full_marks_with_issues
        grade = make_grade(score="100/100", major_issues=["Something wrong"], suggested_improvements=[])
        result = await guardrail_no_full_marks_with_issues(ctx, None, grade)
        assert result.tripwire_triggered

    async def test_full_marks_without_issues_pass(self, ctx, make_grade):
        from src.guardrails import guardrail_no_full_marks_with_issues
        grade = make_grade(score="100/100", major_issues=[], suggested_improvements=[])
        result = await guardrail_no_full_marks_with_issues(ctx, None, grade)
        assert not result.tripwire_triggered

    async def test_corrected_code_valid(self, ctx, make_grade):
        from src.guardrails import guardrail_corrected_code_valid
        grade = make_grade(corrected_code="print('hello')")
        result = await guardrail_corrected_code_valid(ctx, None, grade)
        assert not result.tripwire_triggered

    async def test_corrected_code_syntax_error(self, ctx, make_grade):
        from src.guardrails import guardrail_corrected_code_valid
        grade = make_grade(corrected_code="print 'hello'")
        result = await guardrail_corrected_code_valid(ctx, None, grade)
        assert result.tripwire_triggered

# ===================================================================
# 8. quadrants.py
# ===================================================================


@pytest.mark.asyncio
class TestQuadrants:
    async def test_detect_language_python(self, make_context):
        from src.quadrants import detect_language_and_project_type
        ctx = make_context(file_name="main.py")
        result = await run_tool(detect_language_and_project_type, ctx)
        assert "PYTHON" in result

    async def test_detect_language_javascript(self, make_context):
        from src.quadrants import detect_language_and_project_type
        ctx = make_context(file_name="app.js", student_code="const x = 1; function foo() { return x; }")
        result = await run_tool(detect_language_and_project_type, ctx)
        assert "JAVASCRIPT" in result

    async def test_detect_language_unknown(self, make_context):
        from src.quadrants import detect_language_and_project_type
        ctx = make_context(file_name="data.txt", student_code="some random text no code patterns")
        result = await run_tool(detect_language_and_project_type, ctx)
        assert "Could not determine" in result

    async def test_file_naming_spaces(self, make_context):
        from src.quadrants import check_file_naming_and_structure
        ctx = make_context(file_name="my file.py")
        result = await run_tool(check_file_naming_and_structure, ctx)
        assert "Spaces" in result

    async def test_file_naming_hidden(self, make_context):
        from src.quadrants import check_file_naming_and_structure
        ctx = make_context(file_name=".hidden.py")
        result = await run_tool(check_file_naming_and_structure, ctx)
        assert "hidden" in result.lower()

    async def test_file_naming_special_chars(self, make_context):
        from src.quadrants import check_file_naming_and_structure
        ctx = make_context(file_name="bad!.py")
        result = await run_tool(check_file_naming_and_structure, ctx)
        assert "Special" in result

    async def test_file_naming_missing(self, make_context):
        from src.quadrants import check_file_naming_and_structure
        ctx = make_context(file_name="")
        result = await run_tool(check_file_naming_and_structure, ctx)
        assert "No filename" in result

    async def test_file_structure_no_issues(self, make_context):
        from src.quadrants import check_file_naming_and_structure
        ctx = make_context(file_name="main.py", folder_structure="project/src/")
        result = await run_tool(check_file_naming_and_structure, ctx)
        assert "No filename" not in result

    async def test_logic_analysis_python_input(self, make_context):
        from src.quadrants import analyze_logic_and_output
        ctx = make_context(student_code="x = input('enter: ')\nprint(x)", file_name="test.py")
        result = await run_tool(analyze_logic_and_output, ctx)
        assert "input()" in result

    async def test_logic_analysis_syntax_error(self, make_context):
        from src.quadrants import analyze_logic_and_output
        ctx = make_context(student_code="def broken(\n    pass", file_name="bad.py")
        result = await run_tool(analyze_logic_and_output, ctx)
        assert "SYNTAX" in result

    async def test_logic_analysis_java(self, make_context):
        from src.quadrants import analyze_logic_and_output
        ctx = make_context(student_code="class Main { }", file_name="Main.java")
        result = await run_tool(analyze_logic_and_output, ctx)
        assert "No main method" in result

    async def test_logic_analysis_html(self, make_context):
        from src.quadrants import analyze_logic_and_output
        ctx = make_context(student_code="<html><body>Hello</body></html>", file_name="index.html")
        result = await run_tool(analyze_logic_and_output, ctx)
        assert "No <script>" in result

    async def test_feb_no_architecture(self, make_context):
        from src.quadrants import verify_feb_connection
        ctx = make_context(folder_structure="")
        result = await run_tool(verify_feb_connection, ctx)
        assert "No frontend-backend" in result

    async def test_feb_frontend_only(self, make_context):
        from src.quadrants import verify_feb_connection
        ctx = make_context(folder_structure="frontend/src/")
        result = await run_tool(verify_feb_connection, ctx)
        assert "Frontend" in result or "frontend" in result

    async def test_feb_matching_endpoints(self, make_context):
        from src.quadrants import verify_feb_connection
        code = '''fetch("/api/users")\n@app.route("/api/users")'''
        ctx = make_context(student_code=code, folder_structure="frontend/backend/")
        result = await run_tool(verify_feb_connection, ctx)
        assert "MATCHED" in result

    async def test_check_python_syntax_valid(self, make_context):
        from src.quadrants import check_python_syntax
        ctx = make_context()
        result = await run_tool(check_python_syntax, ctx, '{"code": "print(1)"}')
        assert "No syntax" in result or "SYNTAX" not in result

    async def test_check_python_syntax_invalid(self, make_context):
        from src.quadrants import check_python_syntax
        ctx = make_context()
        result = await run_tool(check_python_syntax, ctx, '{"code": "if True"}')
        assert "SYNTAX ERROR" in result

    async def test_check_assignment_match(self, make_context):
        import json
        from src.quadrants import check_assignment_match
        ctx = make_context()
        args = json.dumps({"code": ctx.student_code})
        result = await run_tool(check_assignment_match, ctx, args)
        assert "met," in result.lower() or "Requirements:" in result

    async def test_quadrant_grading(self, make_context):
        from src.quadrants import quadrant_grading
        ctx = make_context()
        result = await run_tool(quadrant_grading, ctx)
        assert "Total marks:" in result

    async def test_quadrant_grading_empty(self):
        from src.quadrants import quadrant_grading
        from src.models import TeachingContext
        result = await run_tool(quadrant_grading, TeachingContext())
        assert "Total marks: 100" in result

# ===================================================================
# 9. agents/*.py (unit tests — not calling live AI)
# ===================================================================


class TestAgents:
    def test_teaching_assistant_agent_configured(self):
        from src.agents.teaching_assistant import teaching_assistant_agent
        assert teaching_assistant_agent.name == "SMIT ASSISTANT TUTOR"
        assert len(teaching_assistant_agent.handoffs) == 3
        assert len(teaching_assistant_agent.input_guardrails) == 3
        assert len(teaching_assistant_agent.output_guardrails) == 4

    def test_chatbot_agent_configured(self):
        from src.agents.chatbot import chatbot_agent
        assert chatbot_agent.name == "SMIT_Q4_Conversation"
        assert len(chatbot_agent.tools) == 1

    @pytest.mark.asyncio
    async def test_chatbot_get_conversation_summary(self):
        from src.agents.chatbot import get_conversation_summary
        from agents.tool import ToolContext

        impl = get_conversation_summary.on_invoke_tool._invoke_tool_impl

        tc_empty = ToolContext(
            context=[],
            tool_name="get_conversation_summary",
            tool_call_id="test",
            tool_arguments="{}",
        )
        result_empty = await impl(tc_empty, "{}")
        assert "No conversation yet" in result_empty

        tc_with = ToolContext(
            context=[
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "hello"},
            ],
            tool_name="get_conversation_summary",
            tool_call_id="test",
            tool_arguments="{}",
        )
        result_with = await impl(tc_with, "{}")
        assert "1 user messages" in result_with

# ===================================================================
# 10. api/main.py (integration tests with AsyncClient)
# ===================================================================


class TestAPI:
    @pytest.mark.asyncio
    async def test_health(self, http_client):
        resp = await http_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "auth_enabled" in data

    @pytest.mark.asyncio
    async def test_root_no_auth(self, http_client):
        resp = await http_client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "SMIT ASSISTANT TUTOR"

    @pytest.mark.asyncio
    async def test_root_with_auth(self, http_client, auth_headers):
        resp = await http_client.get("/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"] is not None
        assert data["user"]["role"] == "admin"

    @pytest.mark.asyncio
    async def test_login_valid(self, http_client, tmp_data_dir):
        from src.auth import _seed_default_users
        _seed_default_users()
        resp = await http_client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["user"]["username"] == "admin"

    @pytest.mark.asyncio
    async def test_login_invalid(self, http_client):
        resp = await http_client.post("/auth/login", json={"username": "admin", "password": "wrong"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_register_admin_only(self, http_client, tmp_data_dir, seed_users, auth_headers):
        resp = await http_client.post(
            "/auth/register",
            json={"username": "newuser", "password": "pass123", "role": "student"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["username"] == "newuser"

    @pytest.mark.asyncio
    async def test_register_non_admin_forbidden(self, http_client, tmp_data_dir, seed_users):
        from src.auth import authenticate
        result = authenticate("student", "student123")
        assert result is not None
        token, _ = result
        headers = {"Authorization": f"Bearer {token}"}
        resp = await http_client.post(
            "/auth/register",
            json={"username": "another", "password": "pass"},
            headers=headers,
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_register_no_auth(self, http_client):
        resp = await http_client.post(
            "/auth/register",
            json={"username": "x", "password": "x"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_endpoint(self, http_client, auth_headers):
        resp = await http_client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"

    @pytest.mark.asyncio
    async def test_me_no_auth(self, http_client):
        resp = await http_client.get("/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_sessions_crud(self, http_client, auth_headers):
        resp = await http_client.get("/sessions", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

        resp = await http_client.post("/sessions", json={"title": "Test Chat"}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        sid = data["session_id"]

        resp = await http_client.get("/sessions", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        resp = await http_client.delete(f"/sessions/{sid}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["deleted"] == sid

        resp = await http_client.delete("/sessions/nonexistent", headers=auth_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_sessions_require_auth(self, http_client):
        resp = await http_client.get("/sessions")
        assert resp.status_code == 401
        resp = await http_client.post("/sessions", json={"title": "x"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_grade_requires_auth(self, http_client):
        resp = await http_client.post("/grade", json={
            "assignment_instructions": "test", "rubric": "test 10 points", "student_code": "print('hi')",
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_grade_validates_empty_fields(self, http_client, auth_headers):
        resp = await http_client.post("/grade", json={
            "assignment_instructions": "", "rubric": "test", "student_code": "code",
        }, headers=auth_headers)
        assert resp.status_code == 400

        resp = await http_client.post("/grade", json={
            "assignment_instructions": "instr", "rubric": "", "student_code": "code",
        }, headers=auth_headers)
        assert resp.status_code == 400

        resp = await http_client.post("/grade", json={
            "assignment_instructions": "instr", "rubric": "test 10 points", "student_code": "",
        }, headers=auth_headers)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_grade_demo_mode(self, http_client, auth_headers):
        resp = await http_client.post("/grade", json={
            "assignment_instructions": "Create a temperature converter",
            "rubric": "Functions (30), Input (20), Output (20), Error (15), Quality (15)",
            "student_code": "def celsius_to_fahrenheit(c): return (c*9/5)+32",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "score" in data
        score_str = data["score"]
        assert "/" in score_str
        parts = score_str.split("/")
        assert parts[0].isdigit()
        # Score should not be a hardcoded fallback
        assert score_str != "75/100"

    @pytest.mark.asyncio
    async def test_chat_endpoint(self, http_client, auth_headers):
        resp = await http_client.post("/chat", json={
            "session_id": "", "message": "Hello",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert "response" in data
        assert len(data["response"]) > 0

    @pytest.mark.asyncio
    async def test_chat_with_grade_context(self, http_client, auth_headers):
        resp = await http_client.post("/chat", json={
            "session_id": "", "message": "Why did I lose marks?",
            "grade_context": {
                "score": "75/100", "verdict": "Good effort",
                "what_went_well": ["Structure"], "major_issues": ["Error handling"],
                "explanation": "Missing try-except",
            },
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["response"]) > 0

    @pytest.mark.asyncio
    async def test_chat_requires_auth(self, http_client):
        resp = await http_client.post("/chat", json={"session_id": "", "message": "Hi"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_grade_with_full_context(self, http_client, auth_headers):
        resp = await http_client.post("/grade", json={
            "assignment_title": "Temperature Converter",
            "assignment_instructions": "Create a program that converts temperatures.",
            "rubric": "Functions (30 points), Input handling (20), Output (20), Error handling (15), Code quality (15)",
            "total_marks": 100,
            "student_code": "def convert(c): return (c*9/5)+32",
            "file_name": "main.py",
            "folder_structure": "project/src/",
            "expected_output": "Enter temp: 100\n100C = 212F",
            "sample_output": "100C = 212F",
            "previous_feedback": "Use functions next time",
            "class_notes": "Remember to use try-except",
            "common_mistakes": "Forgetting to convert input to float",
            "student_name": "Ali",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "score" in data
        assert len(data["what_went_well"]) > 0

    @pytest.mark.asyncio
    async def test_delete_other_users_session_forbidden(self, http_client, tmp_data_dir):
        from src.auth import authenticate
        admin_result = authenticate("admin", "admin123")
        assert admin_result is not None
        admin_token, _ = admin_result
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        resp = await http_client.post("/sessions", json={"title": "Admin Chat"}, headers=admin_headers)
        sid = resp.json()["session_id"]

        student_result = authenticate("student", "student123")
        assert student_result is not None
        student_token, _ = student_result
        student_headers = {"Authorization": f"Bearer {student_token}"}
        resp = await http_client.delete(f"/sessions/{sid}", headers=student_headers)
        assert resp.status_code == 403
