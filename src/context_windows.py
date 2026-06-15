"""7-window context management system.
Each window is a focused dimension of the agent's context.
The agent explicitly references these windows to maintain awareness."""

from dataclasses import dataclass, field
from typing import Any


WINDOW_SPECS = {
    "W1": {
        "name": "Assignment",
        "description": "Assignment title, full instructions, total marks available",
        "fields": ["assignment_title", "assignment_instructions", "total_marks"],
    },
    "W2": {
        "name": "Code",
        "description": "Student's submitted code, file name, folder structure",
        "fields": ["student_code", "file_name", "folder_structure"],
    },
    "W3": {
        "name": "Rubric",
        "description": "Rubric criteria, point distribution, grading scale — SOURCE OF TRUTH for marks",
        "fields": ["rubric"],
    },
    "W4": {
        "name": "Output",
        "description": "Expected output format, sample output for comparison",
        "fields": ["expected_output", "sample_output"],
    },
    "W5": {
        "name": "History",
        "description": "Previous feedback given to this student on earlier submissions",
        "fields": ["previous_feedback"],
    },
    "W6": {
        "name": "Knowledge",
        "description": "Class notes and common mistakes — for feedback enrichment only, never for marks",
        "fields": ["class_notes", "common_mistakes"],
    },
    "W7": {
        "name": "Session",
        "description": "Student name, conversation history, current evaluation state",
        "fields": ["student_name"],
    },
}


@dataclass
class ContextWindows:
    """Holds the 7 context windows. Each window is a dict of its fields."""

    W1_assignment: dict[str, Any] = field(default_factory=dict)
    W2_code: dict[str, Any] = field(default_factory=dict)
    W3_rubric: dict[str, Any] = field(default_factory=dict)
    W4_output: dict[str, Any] = field(default_factory=dict)
    W5_history: dict[str, Any] = field(default_factory=dict)
    W6_knowledge: dict[str, Any] = field(default_factory=dict)
    W7_session: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_teaching_context(cls, ctx: Any) -> "ContextWindows":
        """Build 7 windows from a TeachingContext dataclass."""
        return cls(
            W1_assignment={
                "title": getattr(ctx, "assignment_title", ""),
                "instructions": getattr(ctx, "assignment_instructions", ""),
                "total_marks": getattr(ctx, "total_marks", 100),
            },
            W2_code={
                "code": getattr(ctx, "student_code", ""),
                "file_name": getattr(ctx, "file_name", ""),
                "folder_structure": getattr(ctx, "folder_structure", ""),
            },
            W3_rubric={
                "rubric_text": getattr(ctx, "rubric", ""),
            },
            W4_output={
                "expected": getattr(ctx, "expected_output", ""),
                "sample": getattr(ctx, "sample_output", ""),
            },
            W5_history={
                "previous_feedback": getattr(ctx, "previous_feedback", ""),
            },
            W6_knowledge={
                "class_notes": getattr(ctx, "class_notes", ""),
                "common_mistakes": getattr(ctx, "common_mistakes", ""),
            },
            W7_session={
                "student_name": getattr(ctx, "student_name", "Student"),
                "status": "pending",
            },
        )

    def render_for_prompt(self) -> str:
        """Render all 7 windows into a prompt string the agent can read."""
        attr_map = {
            "W1": "W1_assignment",
            "W2": "W2_code",
            "W3": "W3_rubric",
            "W4": "W4_output",
            "W5": "W5_history",
            "W6": "W6_knowledge",
            "W7": "W7_session",
        }
        lines = ["=== CONTEXT WINDOWS ==="]
        for key, spec in WINDOW_SPECS.items():
            attr_name = attr_map.get(key)
            window_data = getattr(self, attr_name, {}) if attr_name else {}
            lines.append(f"\n[{key}] {spec['name']} — {spec['description']}")
            if window_data:
                for field_name, value in window_data.items():
                    if value:
                        lines.append(f"  {field_name}: {str(value)[:200]}")
            else:
                lines.append("  (empty)")
        return "\n".join(lines)

    def get_window(self, window_key: str) -> dict:
        mapping = {
            "W1": self.W1_assignment,
            "W2": self.W2_code,
            "W3": self.W3_rubric,
            "W4": self.W4_output,
            "W5": self.W5_history,
            "W6": self.W6_knowledge,
            "W7": self.W7_session,
        }
        return mapping.get(window_key.upper(), {})
