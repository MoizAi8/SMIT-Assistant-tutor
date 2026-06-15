"""Guardrails for the Teaching Assistant agent.
All guardrails anchor to the rubric — the sole source of truth for marks.

3 input guardrails: code_not_empty, rubric_valid, instructions_provided
3 output guardrails: score_rubric_anchored, no_full_marks_with_issues, corrected_code_valid
"""

import ast
import re
from agents import (
    InputGuardrail,
    OutputGuardrail,
    GuardrailFunctionOutput,
    RunContextWrapper,
)
from src.models import TeachingContext, GradingResult


# ─── INPUT GUARDRAILS ─────────────────────────────────────────────

GUARDRAIL_INPUT_MAP = {
    "guardrail_code_not_empty": {
        "window": "W2",
        "field": "code",
        "reason": "No code to evaluate",
    },
    "guardrail_rubric_valid": {
        "window": "W3",
        "field": "rubric_text",
        "reason": "Rubric is the sole source of truth for marks",
    },
    "guardrail_instructions_provided": {
        "window": "W1",
        "field": "instructions",
        "reason": "Cannot grade without knowing the assignment",
    },
}


async def guardrail_code_not_empty(
    ctx: RunContextWrapper[TeachingContext],
    agent,
    input_data: str,
) -> GuardrailFunctionOutput:
    code = ctx.context.student_code.strip() if ctx.context.student_code else ""
    if not code:
        return GuardrailFunctionOutput(
            output_info="[GUARDRAIL BLOCKED] W2: code is empty — nothing to grade.",
            tripwire_triggered=True,
        )
    if len(code) < 10:
        return GuardrailFunctionOutput(
            output_info=f"[GUARDRAIL BLOCKED] W2: code too short ({len(code)} chars).",
            tripwire_triggered=True,
        )
    return GuardrailFunctionOutput(
        output_info="W2: code OK",
        tripwire_triggered=False,
    )


async def guardrail_rubric_valid(
    ctx: RunContextWrapper[TeachingContext],
    agent,
    input_data: str,
) -> GuardrailFunctionOutput:
    rubric = ctx.context.rubric.strip() if ctx.context.rubric else ""
    if not rubric:
        return GuardrailFunctionOutput(
            output_info="[GUARDRAIL BLOCKED] W3: rubric missing — cannot grade without rubric.",
            tripwire_triggered=True,
        )
    has_numbers = bool(re.search(r"\d+", rubric))
    if not has_numbers:
        return GuardrailFunctionOutput(
            output_info="[GUARDRAIL BLOCKED] W3: rubric must contain point values (numbers) to anchor grading.",
            tripwire_triggered=True,
        )
    return GuardrailFunctionOutput(
        output_info="W3: rubric OK",
        tripwire_triggered=False,
    )


async def guardrail_instructions_provided(
    ctx: RunContextWrapper[TeachingContext],
    agent,
    input_data: str,
) -> GuardrailFunctionOutput:
    instructions = (
        ctx.context.assignment_instructions.strip()
        if ctx.context.assignment_instructions
        else ""
    )
    if not instructions:
        return GuardrailFunctionOutput(
            output_info="[GUARDRAIL BLOCKED] W1: no assignment instructions provided.",
            tripwire_triggered=True,
        )
    if len(instructions) < 30:
        return GuardrailFunctionOutput(
            output_info=f"[GUARDRAIL BLOCKED] W1: instructions too short ({len(instructions)} chars).",
            tripwire_triggered=True,
        )
    return GuardrailFunctionOutput(
        output_info="W1: instructions OK",
        tripwire_triggered=False,
    )


# ─── OUTPUT GUARDRAILS ────────────────────────────────────────────

GUARDRAIL_OUTPUT_MAP = {
    "guardrail_score_rubric_anchored": {
        "checks": ["format", "denominator", "exceeds_total"],
        "purpose": "Score must match rubric's total marks and have valid format",
    },
    "guardrail_no_full_marks_with_issues": {
        "checks": ["full_marks_no_issues"],
        "purpose": "Full marks only when no major issues exist",
    },
    "guardrail_corrected_code_valid": {
        "checks": ["code_parses", "code_not_empty"],
        "purpose": "Corrected code must be valid Python",
    },
}


async def guardrail_score_rubric_anchored(
    ctx: RunContextWrapper[TeachingContext],
    agent,
    output: GradingResult,
) -> GuardrailFunctionOutput:
    score_str = output.score.strip()
    if "/" not in score_str:
        return GuardrailFunctionOutput(
            output_info=f"[GUARDRAIL] Score '{score_str}' must be in 'X/Y' format.",
            tripwire_triggered=True,
        )
    try:
        num_str, den_str = score_str.split("/")
        num, den = int(num_str), int(den_str)
    except (ValueError, TypeError):
        return GuardrailFunctionOutput(
            output_info=f"[GUARDRAIL] Score '{score_str}' has non-numeric values.",
            tripwire_triggered=True,
        )

    context_total = ctx.context.total_marks
    if den != context_total:
        return GuardrailFunctionOutput(
            output_info=f"[GUARDRAIL] Score denominator {den} != rubric total marks {context_total}.",
            tripwire_triggered=True,
        )
    if num > den:
        return GuardrailFunctionOutput(
            output_info=f"[GUARDRAIL] Score {num}/{den} exceeds rubric total.",
            tripwire_triggered=True,
        )
    return GuardrailFunctionOutput(
        output_info="score rubric-anchored OK",
        tripwire_triggered=False,
    )


async def guardrail_no_full_marks_with_issues(
    ctx: RunContextWrapper[TeachingContext],
    agent,
    output: GradingResult,
) -> GuardrailFunctionOutput:
    try:
        num = int(output.score.split("/")[0])
        den = int(output.score.split("/")[1])
    except (ValueError, IndexError):
        return GuardrailFunctionOutput(
            output_info="cannot check full marks",
            tripwire_triggered=False,
        )
    if num == den and num > 0:
        if output.major_issues and len([i for i in output.major_issues if i.strip()]) > 0:
            return GuardrailFunctionOutput(
                output_info=f"[GUARDRAIL] Score {num}/{den} but {len(output.major_issues)} major issues present.",
                tripwire_triggered=True,
            )
        if output.suggested_improvements and len(output.suggested_improvements) > 0:
            return GuardrailFunctionOutput(
                output_info=f"[GUARDRAIL] Score {num}/{den} but improvements suggested.",
                tripwire_triggered=True,
            )
    return GuardrailFunctionOutput(
        output_info="score integrity OK",
        tripwire_triggered=False,
    )


async def guardrail_corrected_code_valid(
    ctx: RunContextWrapper[TeachingContext],
    agent,
    output: GradingResult,
) -> GuardrailFunctionOutput:
    code = output.corrected_code.strip() if output.corrected_code else ""
    if not code:
        return GuardrailFunctionOutput(
            output_info="[GUARDRAIL] Corrected code is empty.",
            tripwire_triggered=True,
        )
    try:
        ast.parse(code)
    except SyntaxError as e:
        return GuardrailFunctionOutput(
            output_info=f"[GUARDRAIL] Corrected code has syntax error at line {e.lineno}: {e.msg}.",
            tripwire_triggered=True,
        )
    return GuardrailFunctionOutput(
        output_info="corrected code valid",
        tripwire_triggered=False,
    )


LANGUAGE_KEYWORDS = {
    "python": ["def ", "print(", "import ", "class ", "snake_case", "self", "__init__", "if __name__"],
    "javascript": ["function ", "const ", "let ", "var ", "console.log", "=>", "camelCase", "useState"],
    "typescript": [": string", ": number", "interface ", "type ", "camelCase"],
    "java": ["public class", "public static void", "System.out", "camelCase"],
    "html": ["<html", "<body", "<div", "<script", "<link"],
}


async def guardrail_no_language_confusion(
    ctx: RunContextWrapper[TeachingContext],
    agent,
    output: GradingResult,
) -> GuardrailFunctionOutput:
    """Ensure feedback mentions only the correct language's terminology."""
    from src.config import OPENAI_API_KEY
    if not OPENAI_API_KEY:
        return GuardrailFunctionOutput(output_info="no api key - skip lang check", tripwire_triggered=False)

    code = (ctx.context.student_code or "").lower()
    verdict = (output.verdict or "").lower()
    explanation = (output.explanation or "").lower()
    issues_text = " ".join(i.lower() for i in output.major_issues)
    improvements_text = " ".join(i.lower() for i in output.suggested_improvements)
    all_text = f"{verdict} {explanation} {issues_text} {improvements_text}"

    # Detect actual language from code
    detected_lang = None
    for lang, patterns in LANGUAGE_KEYWORDS.items():
        matches = sum(1 for p in patterns if p.lower() in code)
        if matches >= 2:
            detected_lang = lang
            break
    if not detected_lang:
        return GuardrailFunctionOutput(output_info="cannot determine language", tripwire_triggered=False)

    # Check for wrong terminology in feedback
    wrong_terms = []
    for lang, patterns in LANGUAGE_KEYWORDS.items():
        if lang == detected_lang:
            continue
        for p in patterns:
            if p.lower() in all_text:
                wrong_terms.append(f"'{p}' (from {lang}) mentioned but code is {detected_lang}")

    if wrong_terms:
        return GuardrailFunctionOutput(
            output_info="LANGUAGE CONFUSION: " + "; ".join(wrong_terms[:3]),
            tripwire_triggered=True,
        )

    return GuardrailFunctionOutput(
        output_info="language check passed",
        tripwire_triggered=False,
    )


LANGUAGE_CONFUSION_GUARDRAIL = OutputGuardrail(guardrail_function=guardrail_no_language_confusion)

input_guardrails = [
    InputGuardrail(guardrail_function=guardrail_code_not_empty),
    InputGuardrail(guardrail_function=guardrail_rubric_valid),
    InputGuardrail(guardrail_function=guardrail_instructions_provided),
]

output_guardrails = [
    OutputGuardrail(guardrail_function=guardrail_score_rubric_anchored),
    OutputGuardrail(guardrail_function=guardrail_no_full_marks_with_issues),
    OutputGuardrail(guardrail_function=guardrail_corrected_code_valid),
    LANGUAGE_CONFUSION_GUARDRAIL,
]
