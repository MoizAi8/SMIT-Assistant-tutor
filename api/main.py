"""SMIT ASSISTANT TUTOR API — with JWT auth, role control, and persistent sessions.

Endpoints:
  POST /auth/login       — login, returns JWT token
  POST /auth/register    — register new user (admin only)
  GET  /auth/me          — get current user profile
   POST /grade            — submit code for grading (auth required)
  POST /chat             — chat with TA (auth required)
  GET  /sessions         — list user's chat sessions
  POST /sessions         — create new session
  DELETE /sessions/{id}  — delete a session
  GET  /health           — health check
"""

import uuid, logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents import Runner

from src.config import OPENAI_MODEL
from src.models import TeachingContext, GradingResult, ChatSession, ROLES, GradeRequest, GradeResponse
from src.context_windows import ContextWindows
from src.agents.teaching_assistant import teaching_assistant_agent
from src.agents.chatbot import run_chatbot_session
from src.auth import authenticate, register_user, get_user_from_token, get_user_by_id, User
from src.demo_grader import build_grade_response
from src import session_store as store

logger = logging.getLogger(__name__)

# ─── Request / Response models ─────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "student"
    display_name: str = ""

class AuthResponse(BaseModel):
    token: str
    user: dict

class GradeContext(BaseModel):
    score: str = ""
    verdict: str = ""
    explanation: str = ""
    what_went_well: list[str] = []
    major_issues: list[str] = []

class ChatRequest(BaseModel):
    session_id: str
    message: str
    grade_context: GradeContext | None = None

class ChatResponse(BaseModel):
    session_id: str
    response: str

class HealthResponse(BaseModel):
    status: str
    model: str
    version: str = "1.0.0"
    auth_enabled: bool = True

class SessionCreateRequest(BaseModel):
    title: str = "New Chat"

class SessionListItem(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int

# ─── Auth dependency ───────────────────────────────────────────────

async def get_current_user(authorization: str = Header("")) -> User | None:
    if not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    user = get_user_from_token(token)
    if not user:
        return None
    return user


async def require_auth(current_user: User | None = Depends(get_current_user)) -> User:
    if not current_user:
        raise HTTPException(401, "Missing or invalid Authorization header. Login at /auth/login")
    return current_user

# ─── Demo data ─────────────────────────────────────────────────────

DEMO_CHAT_RESPONSES = [
    "Bilkul! Yeh issue aapke code mein variable naming ka hai. Python mein snake_case use karte hain, yani: my_variable na ke myVariable.",
    "Aapne poochha ke score 75/100 kyun hai? Chaliye batata hoon:\n\nRequirements: 22/30 — zyada cheezein sahi hain\nCorrectness: 24/30 — formulas sahi hain, lekin input conversion miss hai\nCode Quality: 16/20 — naming theek hai, docstrings missing hain\nOutput: 13/20 — output format sahi hai, lekin error handling nahi hai",
    "Bohot acha sawaal hai! Aap try-except ka use karke error handle kar sakte hain:\n\n```python\ntry:\n    temp = float(input(\"Enter temperature: \"))\nexcept ValueError:\n    print(\"Invalid input! Please enter a number.\")\n```",
    "Haan, docstrings add karna acchi practice hai. Bas function ke immediately baad triple quotes mein explain karein.",
    "Mujhe iska pata nahi, lekin main aapko bata sakta hoon ke kaise seekhein: Python ki official documentation dekhein ya W3Schools par practice karein.",
]

# ─── Lifespan ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SMIT ASSISTANT TUTOR API — auth + sessions enabled")
    logger.info(f"  Default users: admin/admin123, teacher/teacher123, student/student123")
    logger.info(f"  Sessions stored in: data/sessions.json")
    mode = "LIVE" if _has_api_key() else "DEMO (mock responses)"
    logger.info(f"  Mode: {mode}")
    yield

app = FastAPI(
    title="SMIT ASSISTANT TUTOR API",
    description="Auth + Role Control + Persistent Sessions | 7 windows | 4 quadrants | 7 guardrails",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Auth endpoints ────────────────────────────────────────────────

@app.post("/auth/login", response_model=AuthResponse, tags=["Auth"])
async def login(req: LoginRequest):
    result = authenticate(req.username, req.password)
    if not result:
        raise HTTPException(401, "Invalid username or password")
    token, user = result
    return AuthResponse(
        token=token,
        user={"id": user.id, "username": user.username, "role": user.role,
              "display_name": user.display_name, "created_at": user.created_at},
    )

@app.post("/auth/register", response_model=AuthResponse, tags=["Auth"])
async def register(req: RegisterRequest, current_user: User = Depends(require_auth)):
    if current_user.role != "admin":
        raise HTTPException(403, "Only admins can register new users")
    if req.role not in ROLES:
        raise HTTPException(400, f"Invalid role. Must be one of: {', '.join(ROLES)}")
    result = register_user(req.username, req.password, req.role, req.display_name)
    if not result:
        raise HTTPException(409, "Username already taken or invalid data")
    token, user = result
    return AuthResponse(
        token=token,
        user={"id": user.id, "username": user.username, "role": user.role,
              "display_name": user.display_name, "created_at": user.created_at},
    )

@app.get("/auth/me", tags=["Auth"])
async def me(current_user: User = Depends(require_auth)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "display_name": current_user.display_name,
        "created_at": current_user.created_at,
    }

# ─── Session endpoints ─────────────────────────────────────────────

@app.get("/sessions", response_model=list[SessionListItem], tags=["Sessions"])
async def list_sessions(current_user: User = Depends(require_auth)):
    sessions = store.get_user_sessions(current_user.id)
    items = []
    for s in sessions:
        items.append(SessionListItem(
            id=s.id, title=s.title, created_at=s.created_at,
            updated_at=s.updated_at, message_count=len(s.history),
        ))
    return items

@app.post("/sessions", tags=["Sessions"])
async def create_session_endpoint(
    req: SessionCreateRequest, current_user: User = Depends(require_auth),
):
    session = store.create_session(current_user.id, req.title)
    return {"session_id": session.id, "title": session.title,
            "created_at": session.created_at}

@app.delete("/sessions/{session_id}", tags=["Sessions"])
async def delete_session_endpoint(
    session_id: str, current_user: User = Depends(require_auth),
):
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(403, "Not your session")
    store.delete_session(session_id)
    return {"deleted": session_id}

# ─── Root / Health ─────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root(current_user: User | None = Depends(get_current_user)):
    return {
        "service": "SMIT ASSISTANT TUTOR",
        "version": "3.0.0",
        "architecture": {
            "context_windows": "7 (W1-W7)",
            "quadrants": "4 with handoffs (Q1-Q4)",
            "guardrails": "7 (3 input + 4 output)",
            "auth": "JWT with admin/teacher/student roles",
            "sessions": "Persistent JSON store",
        },
        "endpoints": {
            "grade": "POST /grade",
            "chat": "POST /chat",
            "auth": "POST /auth/login, GET /auth/me",
            "sessions": "GET/POST /sessions, DELETE /sessions/{id}",
            "health": "GET /health",
        },
        "user": {"id": current_user.id, "role": current_user.role,
                 "display_name": current_user.display_name} if current_user else None,
    }

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", model=OPENAI_MODEL)

# ─── Grade endpoint ───────────────────────────────────────────────

def _has_api_key() -> bool:
    try:
        from src.config import OPENAI_API_KEY
        return bool(OPENAI_API_KEY)
    except Exception:
        return False

@app.post("/grade", response_model=GradeResponse, tags=["Core"])
async def grade_submission(req: GradeRequest, current_user: User = Depends(require_auth)):
    if not req.student_code.strip():
        raise HTTPException(400, "student_code cannot be empty")
    if not req.rubric.strip():
        raise HTTPException(400, "rubric cannot be empty")
    if not req.assignment_instructions.strip():
        raise HTTPException(400, "assignment_instructions cannot be empty")

    result_data = None

    if _has_api_key():
        context = TeachingContext(
            assignment_title=req.assignment_title,
            assignment_instructions=req.assignment_instructions,
            rubric=req.rubric, total_marks=req.total_marks,
            student_code=req.student_code, file_name=req.file_name,
            folder_structure=req.folder_structure,
            expected_output=req.expected_output,
            sample_output=req.sample_output,
            previous_feedback=req.previous_feedback,
            class_notes=req.class_notes,
            common_mistakes=req.common_mistakes,
            student_name=req.student_name or "Student",
        )
        cw = ContextWindows.from_teaching_context(context)
        user_message = (
            f"Grade this submission.\n\n{cw.render_for_prompt()}\n\n"
            f"Follow the workflow: Q1 -> Q2 -> Q3 -> compile GradingResult."
        )
        try:
            result = await Runner.run(teaching_assistant_agent, user_message, context=context)
            grade: GradingResult = result.final_output
            result_data = GradeResponse(
                score=grade.score, verdict=grade.verdict,
                what_went_well=grade.what_went_well,
                major_issues=grade.major_issues,
                explanation=grade.explanation,
                suggested_improvements=grade.suggested_improvements,
                corrected_code=grade.corrected_code,
            )
        except Exception as e:
            err = str(e)
            if "InputGuardrailTripwireTriggered" in err or "tripwire" in err.lower():
                raise HTTPException(422, "Input validation failed. Check rubric, code, and instructions.")
            logger.warning(f"OpenAI grading failed: {type(e).__name__}: {err[:200]}")

    if result_data is None:
        result_data = build_grade_response(req)
        logger.info(f"Demo grader used — score={result_data.score}")

    return result_data

# ─── Chat endpoint ─────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse, tags=["Core"])
async def chat(req: ChatRequest, current_user: User = Depends(require_auth)):
    session_id = req.session_id.strip() or str(uuid.uuid4())

    session = store.get_session(session_id)
    if not session:
        session = store.create_session(current_user.id, f"Chat {session_id[:8]}")

    store.add_message(session_id, "user", req.message)

    grade_for_chat = getattr(session, "last_grade", None)
    if req.grade_context:
        grade_for_chat = GradingResult(
            score=req.grade_context.score or "N/A",
            verdict=req.grade_context.verdict or "No verdict",
            what_went_well=req.grade_context.what_went_well or [],
            major_issues=req.grade_context.major_issues or [],
            explanation=req.grade_context.explanation or "No explanation",
            suggested_improvements=[], corrected_code="",
        )
        store.update_last_grade(session_id, grade_for_chat)

    response_text = ""

    if _has_api_key() and grade_for_chat:
        try:
            response_text = await run_chatbot_session(grade_for_chat, session, req.message)
        except Exception as e:
            logger.warning(f"OpenAI chat failed: {type(e).__name__}: {str(e)[:200]}")

    if not response_text:
        import random
        response_text = DEMO_CHAT_RESPONSES[random.randint(0, len(DEMO_CHAT_RESPONSES) - 1)]

    store.add_message(session_id, "assistant", response_text)
    return ChatResponse(session_id=session_id, response=response_text)

# ─── Entry point ───────────────────────────────────────────────────

def start():
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start()
