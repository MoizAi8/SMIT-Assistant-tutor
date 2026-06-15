"""Quadrant architecture — four specialized sub-agents with handoffs.
  Q1 - Analysis   (language detection, syntax, files, logic, FE/BE connection)
  Q2 - Grading    (rubric comparison, evidence-based scoring, language-aware)
  Q3 - Feedback   (Roman Urdu, suggestions, corrected code, no language confusion)
  Q4 - Conversation (chatbot, session mgmt, context windows)
"""

import ast
import re
from agents import Agent, ModelSettings, function_tool, RunContextWrapper
from src.config import OPENAI_MODEL
from src.models import TeachingContext


# ─── LANGUAGE/PROJECT DETECTION ─────────────────────────────────────

LANGUAGE_SIGNATURES = {
    "python": {
        "extensions": [".py", ".pyw"],
        "patterns": [r"\bdef\s+\w+\s*\(", r"\bimport\s+\w+", r"\bfrom\s+\w+\s+import", r"\bclass\s+\w+", r"print\s*\(", r"if\s+__name__\s*==", r"#.*coding"],
        "files": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile", "manage.py"],
        "comment": "#",
    },
    "javascript": {
        "extensions": [".js", ".mjs", ".cjs"],
        "patterns": [r"\bfunction\s+\w+\s*\(", r"\bconst\b", r"\blet\b", r"\bvar\b", r"=>\s*{", r"module\.exports", r"require\s*\(", r"console\.log"],
        "files": ["package.json", ".eslintrc", "webpack.config.js", "vite.config.js"],
        "comment": "//",
    },
    "typescript": {
        "extensions": [".ts", ".tsx"],
        "patterns": [r":\s*(string|number|boolean|void|any)\b", r"\binterface\s+\w+", r"\btype\s+\w+\s*=", r"\bimport\s+.*\bfrom\b"],
        "files": ["tsconfig.json", "package.json"],
        "comment": "//",
    },
    "react": {
        "extensions": [".jsx", ".tsx"],
        "patterns": [r"import\s+React", r"export\s+default", r"const\s+\w+\s*=\s*\(", r"<[A-Z]\w+", r"useState", r"useEffect", r"return\s*\("],
        "files": ["package.json"],
        "comment": "//",
    },
    "html": {
        "extensions": [".html", ".htm"],
        "patterns": [r"<!DOCTYPE", r"<html", r"<head", r"<body", r"<div", r"<script"],
        "files": ["index.html"],
        "comment": "<!--",
    },
    "css": {
        "extensions": [".css", ".scss", ".less"],
        "patterns": [r"\{[\s\S]*\}", r"@media", r":\s*\w+;", r"\.[\w-]+\s*\{"],
        "comment": "/*",
    },
    "java": {
        "extensions": [".java"],
        "patterns": [r"\bpublic\s+class\b", r"\bpublic\s+static\s+void\s+main", r"\bSystem\.out\.print", r"\bimport\s+java"],
        "files": ["pom.xml", "build.gradle", "AndroidManifest.xml"],
        "comment": "//",
    },
    "sql": {
        "extensions": [".sql"],
        "patterns": [r"\bSELECT\b", r"\bFROM\b", r"\bCREATE\s+TABLE", r"\bINSERT\s+INTO"],
        "comment": "--",
    },
    "cpp": {
        "extensions": [".cpp", ".cxx", ".h", ".hpp"],
        "patterns": [r"#include", r"\bint\s+main\s*\(", r"\bstd::", r"\bcout\b"],
        "files": ["CMakeLists.txt", "Makefile"],
        "comment": "//",
    },
}

PROJECT_TYPES = {
    "cli": ["main", "cli", "command", "console", "terminal"],
    "web_frontend": ["react", "vue", "angular", "html", "css", "frontend", "ui"],
    "web_backend": ["api", "flask", "django", "express", "backend", "server"],
    "fullstack": ["fullstack", "full stack", "web app", "next"],
    "data_science": ["data", "analysis", "ml", "machine learning", "jupyter"],
    "mobile": ["mobile", "android", "ios", "flutter"],
    "script": ["script", "automation", "tool", "utility"],
}


@function_tool
def detect_language_and_project_type(ctx: RunContextWrapper[TeachingContext]) -> str:
    """Detect the programming language and project type from code, filename, and folder structure."""
    code = ctx.context.student_code or ""
    file_name = ctx.context.file_name or ""
    folder = ctx.context.folder_structure or ""
    instructions = (ctx.context.assignment_instructions or "").lower()

    detected = {}
    for lang, sig in LANGUAGE_SIGNATURES.items():
        score = 0
        if any(file_name.endswith(ext) for ext in sig["extensions"]):
            score += 3
        matches = sum(1 for p in sig["patterns"] if re.search(p, code))
        score += matches
        if any(f in folder.lower() or f in file_name.lower() for f in sig.get("files", [])):
            score += 2
        if score > 0:
            detected[lang] = score

    if not detected:
        return "LANGUAGE: Could not determine — treat as generic code."

    sorted_langs = sorted(detected.items(), key=lambda x: -x[1])
    primary = sorted_langs[0][0]

    comment = LANGUAGE_SIGNATURES.get(primary, {}).get("comment", "#")
    project_type = "general"
    for ptype, keywords in PROJECT_TYPES.items():
        if any(kw in instructions for kw in keywords):
            project_type = ptype
            break
    if any(kw in folder.lower() for kw in ["frontend", "client", "ui"]):
        project_type = "web_frontend" if project_type != "fullstack" else project_type
    if any(kw in folder.lower() for kw in ["backend", "server", "api"]):
        project_type = "web_backend" if project_type != "fullstack" else project_type

    result = [
        f"DETECTED LANGUAGE: {primary.upper()} (confidence: {sorted_langs[0][1]})",
        f"PROJECT TYPE: {project_type.replace('_', ' ').title()}",
        f"FILE EXTENSION: {LANGUAGE_SIGNATURES.get(primary, {}).get('extensions', ['unknown'])[0]}",
        f"COMMENT SYNTAX: {comment}",
    ]
    if len(sorted_langs) > 1:
        result.append(f"OTHER DETECTED: {', '.join(f'{l}({s})' for l,s in sorted_langs[1:3])}")
    return "\n".join(result)


# ─── Q1: ANALYSIS AGENT ───────────────────────────────────────────

Q1_INSTRUCTIONS = """You are Q1-Analysis, a code analysis specialist. Your ONLY job is to analyze student submissions thoroughly.

## New Workflow — Always follow this order:

### Step 1: Detect Language & Project
Use `detect_language_and_project_type` FIRST to identify the programming language and project type. This determines ALL subsequent checks.

### Step 2: Check File Organization
Use `check_file_naming_and_structure` to validate filenames, folder structure, and detect missing expected files.

### Step 3: Analyze Code
Use the language-appropriate tools:
- For Python: check syntax with AST parsing, naming, completeness, runtime issues
- For JavaScript/TS: check syntax via patterns, naming conventions (camelCase), module structure
- For any language: check logic, validation, input handling, output correctness via `analyze_logic_and_output`

### Step 4: Check FE/BE Connection (if applicable)
If the project has BOTH frontend and backend code, use `verify_feb_connection` to check they're connected properly.

### Step 5: Cross-Reference
Compare assignment title, description, rubric, expected output, and actual code. Report mismatches.

## Critical Rules
- NEVER give Python-specific feedback for JavaScript code (and vice versa)
- Reference file names, line numbers, and folder structure in every finding
- If language is uncertain, flag it clearly
- Do NOT assign scores — that's Q2's job
- Do NOT generate feedback — that's Q3's job

Output a detailed, structured report with clear evidence for every finding."""


@function_tool
def check_file_naming_and_structure(ctx: RunContextWrapper[TeachingContext]) -> str:
    """Check file naming conventions, folder structure, and detect missing expected files."""
    file_name = ctx.context.file_name or ""
    folder = ctx.context.folder_structure or ""
    instructions = ctx.context.assignment_instructions or ""
    rubric = ctx.context.rubric or ""
    code = ctx.context.student_code or ""

    issues = []
    passed = []

    # 1. File name checks
    if file_name:
        if " " in file_name:
            issues.append(f"[FILE] Spaces in filename '{file_name}' — use underscores or hyphens")
        if file_name.startswith("."):
            issues.append(f"[FILE] '{file_name}' is a hidden file — rename it")
        bad_chars = set("!@#$%^&*()+={}[]|\\:;\"'<>,?/~`")
        if any(c in file_name for c in bad_chars):
            issues.append(f"[FILE] Special characters in '{file_name}' — use only letters, numbers, _ and -")
    else:
        issues.append("[FILE] No filename provided — cannot validate naming")

    # 2. Folder structure
    if folder:
        if " " in folder and "/" not in folder and "\\" not in folder:
            issues.append("[STRUCTURE] Folder path contains spaces — use underscores")
    else:
        passed.append("[STRUCTURE] No folder structure to check (optional)")

    # 3. Detect missing expected files from rubric/instructions
    expected_files = re.findall(r"(\w+\.\w+)", instructions + "\n" + rubric)
    expected_files = list(set(f.lower() for f in expected_files if len(f) > 3))
    if expected_files:
        for exp in expected_files:
            if exp not in (file_name.lower() + "\n" + folder.lower()):
                issues.append(f"[MISSING] Expected file '{exp}' not found in submission")

    # 4. Check for common structural patterns based on language
    code_lower = code.lower()
    if "if __name__" in code_lower and not file_name.endswith(".py"):
        pass  # OK for Python
    if "def " in code_lower and "react" not in folder.lower():
        has_funcs = any(isinstance(n, ast.FunctionDef) for n in ast.walk(ast.parse(code))) if code.strip() else False
        if not has_funcs and "def " in code_lower:
            pass  # uses def keyword, has functions
    if "const " in code_lower or "let " in code_lower:
        if not file_name.endswith((".js", ".ts", ".jsx", ".tsx")):
            if file_name.endswith(".py"):
                issues.append("[LANG] JavaScript-style 'const' used in .py file — possible language confusion")

    result = "=== FILE & STRUCTURE ANALYSIS ===\n"
    if passed:
        result += "\n".join(f"  [OK] {p}" for p in passed) + "\n"
    if issues:
        result += "\n".join(f"  [!] {i}" for i in issues) + "\n"
    if not issues and not passed:
        result += "  No file/structure issues found.\n"

    return result


@function_tool
def analyze_logic_and_output(ctx: RunContextWrapper[TeachingContext]) -> str:
    """Analyze code logic, validation patterns, and output correctness. Language-aware."""
    code = ctx.context.student_code or ""
    file_name = ctx.context.file_name or ""
    expected_output = ctx.context.expected_output or ""
    sample_output = ctx.context.sample_output or ""

    issues = []
    observations = []

    # Determine language
    is_python = file_name.endswith(".py") or "def " in code
    is_js = file_name.endswith((".js", ".jsx", ".mjs"))
    is_ts = file_name.endswith((".ts", ".tsx"))
    is_html = file_name.endswith((".html", ".htm"))
    is_java = file_name.endswith(".java")

    # Language-specific checks
    if is_python:
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    fn = node.func
                    if isinstance(fn, ast.Name):
                        if fn.id == "input":
                            parent_call = None
                            for n2 in ast.walk(tree):
                                if isinstance(n2, ast.Call) and n2.func == fn:
                                    parent_call = n2
                                    break
                            observations.append("[LOGIC] input() used — ensure result is converted with int()/float() for math")
                        if fn.id == "print":
                            observations.append("[OUTPUT] print() used for output")
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Constant) and child.value == 0:
                            issues.append("[LOGIC] Division by zero detected — will crash at runtime")
        except SyntaxError as e:
            issues.append(f"[SYNTAX] Code has error at line {e.lineno}: {e.msg}")
    elif is_js or is_ts:
        if "console.log" in code:
            observations.append("[OUTPUT] console.log used for output")
        if "prompt(" in code:
            observations.append("[LOGIC] prompt() used — result is a string, use parseInt()/Number() for numbers")
        if "+" in code and any(kw in code for kw in ["prompt", "input", "value"]):
            observations.append("[LOGIC] String concatenation with + may cause issues with numbers — use template literals or Number()")
        if "fetch(" in code or "axios" in code:
            observations.append("[CONNECTION] fetch/axios used for API calls — check endpoints")
        if "useEffect" in code or "useState" in code:
            observations.append("[REACT] React hooks detected — check dependency arrays")
    elif is_html:
        if "<script" not in code:
            observations.append("[HTML] No <script> tag found — interactive features may not work")
        if "<link" not in code and "<style" not in code:
            observations.append("[HTML] No CSS linked — page may lack styling")
    elif is_java:
        if "public static void main" not in code:
            issues.append("[LOGIC] No main method — program has no entry point")
        if "Scanner" in code and "System.in" not in code:
            observations.append("[INPUT] Scanner created but not connected to System.in")

    # Output comparison
    if sample_output and code:
        # Look for similar output patterns
        sample_clean = sample_output.lower().strip()
        if sample_clean not in code.lower():
            observations.append(f"[OUTPUT] Expected output '{sample_output[:50]}...' — verify code produces this exactly")
    if expected_output:
        expected_clean = expected_output.lower().strip()
        if expected_clean and expected_clean not in code.lower():
            pass  # soft check

    # Validation checks
    if any(kw in code.lower() for kw in ["try", "except", "catch", "if __name__"]):
        observations.append("[VALIDATION] Error handling patterns detected — good practice")
    else:
        if "input" in code or "prompt" in code:
            observations.append("[VALIDATION] No error handling for user input — consider try/except or try/catch")

    result = "=== LOGIC & OUTPUT ANALYSIS ===\n"
    for o in observations:
        result += f"  [i] {o}\n"
    for i in issues:
        result += f"  [!] {i}\n"
    if not observations and not issues:
        result += "  No specific logic issues detected.\n"
    return result


@function_tool
def verify_feb_connection(ctx: RunContextWrapper[TeachingContext]) -> str:
    """If the project has both frontend and backend code, verify they are properly connected."""
    code = ctx.context.student_code or ""
    folder = ctx.context.folder_structure or ""
    file_name = ctx.context.file_name or ""

    result_parts = ["=== FE/BE CONNECTION VERIFICATION ==="]
    has_frontend = False
    has_backend = False
    backend_endpoints = []
    frontend_calls = []

    # Check from folder structure
    folder_lower = folder.lower()
    if any(kw in folder_lower for kw in ["frontend", "client", "ui", "react", "vue"]):
        has_frontend = True
    if any(kw in folder_lower for kw in ["backend", "server", "api", "flask", "django", "express"]):
        has_backend = True

    # Check from code
    if any(kw in code for kw in ["fetch(", "axios.", "XMLHttpRequest", "useEffect"]):
        has_frontend = True
        urls = re.findall(r'["\'](/api/[\w/]+)["\']', code)
        urls += re.findall(r'["\'](http://localhost:\d+/[\w/]+)["\']', code)
        for u in urls:
            frontend_calls.append(u)
    if any(kw in code for kw in ["@app.route", "@api", "app.get(", "app.post(", "router.get", "router.post", "app.use"]):
        has_backend = True
        routes = re.findall(r'["\'](/[\w/]+)["\']', code)
        for r in routes:
            if r.startswith("/"):
                backend_endpoints.append(r)

    if not has_frontend and not has_backend:
        result_parts.append("  No frontend-backend architecture detected in this submission.")
        return "\n".join(result_parts)

    result_parts.append(f"  Frontend detected: {'YES' if has_frontend else 'NO'}")
    result_parts.append(f"  Backend detected:  {'YES' if has_backend else 'NO'}")

    if has_frontend and has_backend:
        # Check for connection
        if frontend_calls:
            result_parts.append(f"\n  Frontend API calls found: {len(frontend_calls)}")
            for u in frontend_calls[:5]:
                matched = any(u.endswith(b) or b.endswith(u) for b in backend_endpoints) if backend_endpoints else False
                status = "MATCHED" if matched else "UNMATCHED"
                result_parts.append(f"    {u} — {status}")
        else:
            result_parts.append("\n  [WARN] Frontend detected but no API calls (fetch/axios) found")

        if backend_endpoints:
            result_parts.append(f"  Backend routes found: {len(backend_endpoints)}")
            for r in backend_endpoints[:5]:
                result_parts.append(f"    {r}")
        else:
            result_parts.append("\n  [WARN] Backend detected but no API routes found")

        if frontend_calls and backend_endpoints:
            unmatched = [u for u in frontend_calls if not any(u.endswith(b) or b.endswith(u) for b in backend_endpoints)]
            if unmatched:
                result_parts.append(f"\n  [ISSUE] {len(unmatched)} frontend call(s) have no matching backend route:")
                for u in unmatched[:3]:
                    result_parts.append(f"    {u}")
            else:
                result_parts.append("\n  [OK] All frontend API calls have matching backend routes")
    else:
        if has_frontend and not has_backend:
            result_parts.append("\n  Frontend-only submission — no backend to verify connection")
        elif has_backend and not has_frontend:
            result_parts.append("\n  Backend-only submission — no frontend to verify connection")

    return "\n".join(result_parts)


@function_tool
def check_python_syntax(ctx: RunContextWrapper[TeachingContext], code: str) -> str:
    """Check Python code for syntax errors using AST parsing."""
    try:
        ast.parse(code)
        return "SYNTAX: No syntax errors. Code is valid Python."
    except SyntaxError as e:
        return f"SYNTAX ERROR at line {e.lineno}: {e.msg}\n  Code: {e.text}"


q1_analysis_agent = Agent[TeachingContext](
    name="SMIT_Q1_Analysis",
    instructions=Q1_INSTRUCTIONS,
    model=OPENAI_MODEL,
    tools=[
        detect_language_and_project_type,
        check_file_naming_and_structure,
        analyze_logic_and_output,
        verify_feb_connection,
        check_python_syntax,
    ],
    model_settings=ModelSettings(temperature=0.1),
)


# ─── Q2: GRADING AGENT ────────────────────────────────────────────

Q2_INSTRUCTIONS = """You are Q2-Grading, a rubric specialist. Your ONLY job is to compare the submission against the rubric.

## Workflow
1. Read W3 (Rubric) — this is the SOLE SOURCE OF TRUTH for marks
2. Read W2 (Code) — find evidence for each rubric criterion
3. Read Language Detection results — grade based on CORRECT language expectations
4. Assign partial or full points per criterion based on VISIBLE EVIDENCE ONLY

## Language-Aware Grading
- If code is Python: check for def, classes, proper indentation, snake_case
- If code is JavaScript/TypeScript: check for function/const, camelCase, module exports
- If code is HTML: check for tags, structure, attributes
- NEVER grade Python code against JavaScript rubric criteria (and vice versa)
- Flag it if language doesn't match the assignment requirements

## Critical Rules
- NEVER invent marks — every point must come from the rubric
- NEVER give full marks unless criterion is fully satisfied
- If no visible evidence exists for a criterion, score 0 for that criterion
- Compare assignment title, description, rubric, expected output, and actual code for consistency

## Output
A structured evidence report: which criteria were met, partially met, or missed.
The FINAL SCORE is calculated by summing points across all rubric criteria."""


@function_tool
def check_assignment_match(ctx: RunContextWrapper[TeachingContext], code: str) -> str:
    """Check code against assignment requirements line by line."""
    instructions = ctx.context.assignment_instructions
    rubric = ctx.context.rubric
    all_lines = (instructions + "\n" + rubric).splitlines()
    requirements = [
        l.strip() for l in all_lines
        if l.strip() and any(kw in l.lower() for kw in [
            "must", "should", "require", "need", "implement",
            "create", "write", "add", "include", "define", "use", "function"
        ])
    ]
    if not requirements:
        requirements = [l.strip() for l in all_lines if l.strip()]
    code_lower = code.lower()
    met, missed, partial = [], [], []
    for req in requirements:
        words = [w.strip(".,;:!?()[]{}\"'") for w in req.lower().split() if len(w) > 3]
        matched = sum(1 for w in words if w in code_lower)
        ratio = matched / len(words) if words else 0
        if ratio >= 0.6:
            met.append(req)
        elif ratio >= 0.3:
            partial.append(req)
        else:
            missed.append(req)
    result = f"Requirements: {len(met)} met, {len(partial)} partial, {len(missed)} missed\n"
    for r in met:
        result += f"  [OK] {r[:80]}\n"
    for r in partial:
        result += f"  [~] {r[:80]} (partial)\n"
    for r in missed:
        result += f"  [X] {r[:80]}\n"
    return result


@function_tool
def quadrant_grading(ctx: RunContextWrapper[TeachingContext]) -> str:
    """Structured rubric evidence gathering."""
    rubric = ctx.context.rubric
    code = ctx.context.student_code
    total = ctx.context.total_marks
    lines = [l.strip() for l in rubric.splitlines() if l.strip()]
    criteria = [l for l in lines if any(c in l for c in "0123456789")]
    code_lower = code.lower()
    parts = [f"Total marks: {total}", f"Rubric criteria found: {len(criteria)}", ""]
    for c in criteria[:8]:
        words = [w.strip(".,;:!?()[]{}") for w in c.lower().split() if len(w) > 3]
        evidence = [w for w in words if w in code_lower]
        if evidence:
            parts.append(f"  [EVIDENCE FOUND] {c[:70]}")
            parts.append(f"    Keywords: {', '.join(evidence[:4])}")
        else:
            parts.append(f"  [NO EVIDENCE] {c[:70]}")
    return "\n".join(parts)


q2_grading_agent = Agent[TeachingContext](
    name="SMIT_Q2_Grading",
    instructions=Q2_INSTRUCTIONS,
    model=OPENAI_MODEL,
    tools=[check_assignment_match, quadrant_grading],
    model_settings=ModelSettings(temperature=0.1),
)


# ─── Q3: FEEDBACK AGENT ───────────────────────────────────────────

Q3_INSTRUCTIONS = """You are Q3-Feedback, a student communication specialist. Your ONLY job is to generate encouraging, beginner-friendly feedback.

## Input
- W6 (Knowledge) for enrichment — class notes + common mistakes
- Analysis report from Q1 (language detected, file issues, logic findings, FE/BE status)
- Grading evidence from Q2
- Final score from the orchestrator

## CRITICAL: Language-Aware Feedback
- NEVER give Python feedback for JavaScript code
- NEVER mention "snake_case" for JavaScript code (JS uses camelCase)
- NEVER mention "def" for non-Python code
- NEVER mention "console.log" for Python code
- ALWAYS use the DETECTED LANGUAGE's terminology:
  * Python: functions (def), snake_case, docstrings, print(), input()
  * JavaScript: functions (function/const), camelCase, comments, console.log, prompt()
  * HTML: tags, elements, attributes, scripts
  * Java: classes, methods, camelCase, System.out.println()
- If language is unclear, use generic terms like "code", "function", "output"

## Output Rules
1. SIMPLE ENGLISH + ROMAN URDU — explain concepts in both
2. Start with STRENGTHS — what went well (with file/line evidence)
3. Then ISSUES — specific, with file names, line numbers, and how to fix
4. Explain WHY it matters, not just WHAT is wrong
5. End with IMPROVEMENTS — actionable, practical steps
6. CORRECTED CODE — full corrected version with fixes applied (in the correct language!)

## Tone
- Friendly teacher, not a robot
- "Yeh behtar ho sakta hai" not "Yeh galat hai"
- "Aap" for respect
- Reference class notes where relevant
- Never mention marks — that's Q2's job

Generate: what_went_well, major_issues, explanation, suggested_improvements, corrected_code."""


@function_tool
def get_knowledge_base_hints(ctx: RunContextWrapper[TeachingContext], code: str) -> str:
    """Get relevant common mistakes and class notes for feedback enrichment only."""
    from src.knowledge_base import get_hints_for_code, get_notes_for_code
    hints = get_hints_for_code(code)
    notes = get_notes_for_code(code)
    parts = ["[KNOWLEDGE BASE — for feedback enrichment only, NOT for marks]"]
    if hints:
        parts.append("\nCommon mistakes to mention:")
        for h in hints[:4]:
            parts.append(f"  - {h}")
    if notes:
        parts.append("\nClass notes to reference:")
        for n in notes[:4]:
            parts.append(f"  - {n}")
    return "\n".join(parts)


@function_tool
def get_current_date(ctx: RunContextWrapper[TeachingContext]) -> str:
    """Get the current date."""
    from datetime import date
    return f"Today is {date.today().isoformat()}."


q3_feedback_agent = Agent[TeachingContext](
    name="SMIT_Q3_Feedback",
    instructions=Q3_INSTRUCTIONS,
    model=OPENAI_MODEL,
    tools=[get_knowledge_base_hints, get_current_date],
    model_settings=ModelSettings(temperature=0.4),
)
