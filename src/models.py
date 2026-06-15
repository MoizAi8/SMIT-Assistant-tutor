from pydantic import BaseModel
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timezone


@dataclass
class TeachingContext:
    assignment_title: str = ""
    assignment_instructions: str = ""
    rubric: str = ""
    total_marks: int = 100
    student_code: str = ""
    file_name: str = ""
    folder_structure: str = ""
    expected_output: str = ""
    sample_output: str = ""
    previous_feedback: str = ""
    class_notes: str = ""
    common_mistakes: str = ""
    student_name: str = "Student"


class GradeRequest(BaseModel):
    assignment_title: str = ""
    assignment_instructions: str
    rubric: str
    total_marks: int = 100
    student_code: str
    file_name: str = ""
    folder_structure: str = ""
    expected_output: str = ""
    sample_output: str = ""
    previous_feedback: str = ""
    class_notes: str = ""
    common_mistakes: str = ""
    student_name: str = "Student"


class GradeResponse(BaseModel):
    score: str
    verdict: str
    what_went_well: list[str]
    major_issues: list[str]
    explanation: str
    suggested_improvements: list[str]
    corrected_code: str


class GradingResult(BaseModel):
    score: str
    verdict: str
    what_went_well: list[str]
    major_issues: list[str]
    explanation: str
    suggested_improvements: list[str]
    corrected_code: str


ROLES = ["admin", "teacher", "student"]


@dataclass
class User:
    id: str
    username: str
    password_hash: str
    role: str = "student"
    display_name: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.display_name:
            self.display_name = self.username
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class ChatSession:
    id: str
    user_id: str
    title: str
    history: list[dict] = field(default_factory=list)
    max_history: int = 20
    last_grade: "GradingResult | None" = None
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-(self.max_history * 2):]
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def get_context_window(self) -> list[dict]:
        return self.history[-self.max_history * 2:]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "history": self.history[-10:],
            "last_grade": self.last_grade.model_dump() if self.last_grade else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
