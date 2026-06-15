import ast
from agents import function_tool, RunContextWrapper
from src.models import TeachingContext
from src.knowledge_base import get_hints_for_code, get_notes_for_code


@function_tool
def check_python_syntax(ctx: RunContextWrapper[TeachingContext], code: str) -> str:
    """Check Python code for syntax errors using AST parsing."""
    try:
        ast.parse(code)
        return "No syntax errors found. Code is valid Python."
    except SyntaxError as e:
        return (
            f"Syntax error at line {e.lineno}: {e.msg}\n"
            f"Code: {e.text}"
        )


@function_tool
def analyze_code_quality(ctx: RunContextWrapper[TeachingContext], code: str) -> str:
    """Analyze naming, imports, structure quality."""
    issues = []
    tree = ast.parse(code)

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            name = node.id
            if name != name.lower() and not name.isupper() and not name.startswith("_"):
                issues.append(
                    f"Line {node.lineno}: '{name}' uses mixed case. "
                    f"Python mein snake_case use hota hai."
                )

    imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    if not imports:
        pass

    if not issues:
        return "Code quality is fine."

    return "\n".join(issues)


@function_tool
def check_assignment_match(ctx: RunContextWrapper[TeachingContext], code: str) -> str:
    """Check code against assignment requirements."""
    instructions = ctx.context.assignment_instructions
    rubric = ctx.context.rubric

    lines = (instructions + "\n" + rubric).splitlines()
    requirements = [l.strip() for l in lines if l.strip() and any(
        kw in l.lower() for kw in ["must", "should", "require", "need",
                                     "implement", "create", "write", "add",
                                     "include", "define", "use", "function"]
    )]

    if not requirements:
        requirements = [l.strip() for l in (instructions + "\n" + rubric).splitlines() if l.strip()]

    code_lower = code.lower()
    met, missed = [], []

    for req in requirements:
        words = [w.strip(".,;:!?()[]{}\"'") for w in req.lower().split() if len(w) > 3]
        if any(w in code_lower for w in words):
            met.append(req)
        else:
            missed.append(req)

    result = f"Requirements met: {len(met)}/{len(requirements)}\n"
    for r in met:
        result += f"  [OK] {r}\n"
    if missed:
        result += f"Missing ({len(missed)}):\n"
        for r in missed:
            result += f"  [MISS] {r}\n"

    return result


@function_tool
def check_completeness(ctx: RunContextWrapper[TeachingContext], code: str) -> str:
    """Check if the submission is complete or partial."""
    issues = []

    if not code or len(code.strip()) == 0:
        return "Submission is EMPTY. No code provided."

    tree = ast.parse(code)
    has_functions = any(isinstance(n, ast.FunctionDef) for n in ast.walk(tree))
    has_main_call = any(
        isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
        and isinstance(n.value.func, ast.Name) and n.value.func.id == "main"
        for n in ast.walk(tree)
    )
    has_input = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "input" for n in ast.walk(tree))
    has_print = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "print" for n in ast.walk(tree))

    if not has_functions:
        issues.append("No functions defined. Assignment likely needs at least one function.")
    if not has_main_call:
        issues.append("No main() call found. Program won't run automatically.")
    if has_input and not has_print:
        issues.append("Takes input but doesn't print output.")

    if not issues:
        return "Submission appears structurally complete."

    return "\n".join(issues) if issues else "Submission appears complete."


@function_tool
def check_runtime_issues(ctx: RunContextWrapper[TeachingContext], code: str) -> str:
    """Analyze code for potential runtime errors without executing."""
    issues = []
    tree = ast.parse(code)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id == "input":
                parent = node
                for child in ast.walk(parent):
                    if isinstance(child, ast.BinOp) and isinstance(child.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
                        if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "input"
                               for n in ast.walk(child)):
                            issues.append(f"Line {node.lineno}: input() returns a string. "
                                           "Use int(input()) for numbers before math operations.")

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            for child in ast.walk(node):
                if isinstance(child, ast.Constant) and child.value == 0:
                    issues.append(f"Line {node.lineno}: Division by zero detected.")

    if not issues:
        return "No obvious runtime issues detected."

    return "\n".join(issues)


@function_tool
def check_file_naming(ctx: RunContextWrapper[TeachingContext], file_name: str) -> str:
    """Check if the submitted file name follows conventions."""
    issues = []

    if not file_name:
        return "No file name provided to check."

    if " " in file_name:
        issues.append("File name contains spaces. Use underscores instead.")

    if not file_name.endswith(".py"):
        issues.append(f"File '{file_name}' should end with .py for Python files.")

    if file_name.startswith("."):
        issues.append("File name starts with a dot (hidden file).")

    lower_name = file_name.lower()
    if any(c in lower_name for c in "!@#$%^&*()+={}[]|\\:;\"'<>,?/~`"):
        issues.append("File name has special characters. Use only letters, numbers, underscores, and hyphens.")

    if not issues:
        return f"File name '{file_name}' looks good."

    return "\n".join(issues)


@function_tool
def check_folder_structure(ctx: RunContextWrapper[TeachingContext], folder_structure: str) -> str:
    """Check if folder structure matches expected layout."""
    if not folder_structure:
        return "No folder structure provided to check."

    instructions = ctx.context.assignment_instructions.lower()
    structure_lower = folder_structure.lower()

    mentioned_dirs = []
    for word in ["folder", "directory", "inside", "submission", "project"]:
        if word in instructions:
            for line in ctx.context.assignment_instructions.splitlines():
                if word in line.lower():
                    mentioned_dirs.append(line.strip())

    if mentioned_dirs:
        for expected in mentioned_dirs:
            expected_lower = expected.lower()
            if expected_lower not in structure_lower:
                return f"Expected structure mention: '{expected}' not found in submitted structure."

    return "Folder structure check passed."


@function_tool
def get_knowledge_base_hints(ctx: RunContextWrapper[TeachingContext], code: str) -> str:
    """Get relevant common mistakes and class notes for the code.
    This is ONLY for improving feedback quality, NEVER for marking."""
    hints = get_hints_for_code(code)
    notes = get_notes_for_code(code)

    result = "=== Knowledge Base Notes (for feedback enrichment only) ===\n"
    if hints:
        result += "Common reminders for the student:\n"
        for h in hints:
            result += f"  - {h}\n"
    if notes:
        result += "\nClass notes reminders:\n"
        for n in notes:
            result += f"  - {n}\n"

    return result


@function_tool
def get_current_date(ctx: RunContextWrapper[TeachingContext]) -> str:
    from datetime import date
    return f"Today is {date.today().isoformat()}."
