"""Demo grader — computes code scores without OpenAI.
Scales with total_marks across 6 weighted categories:
  - Compatibility (15%) — language match, syntax
  - Correctness  (25%) — input handling, output, logic
  - File Structure (10%) — naming, organization
  - Requirements  (30%) — rubric keyword coverage
  - Code Quality  (10%) — functions, naming, docs
  - Cleanliness   (10%) — consistency, formatting
"""

import ast
import re
from src.models import GradeRequest, GradeResponse

LANGUAGE_PATTERNS = {
    "python": {"extensions": [".py", ".pyw"], "keywords": ["def ", "import ", "class ", "print("]},
    "javascript": {"extensions": [".js", ".mjs"], "keywords": ["function ", "const ", "let ", "=>"]},
    "react": {"extensions": [".jsx", ".tsx"], "keywords": ["import React", "useState", "useEffect"]},
    "typescript": {"extensions": [".ts", ".tsx"], "keywords": [": string", ": number", "interface"]},
    "html": {"extensions": [".html", ".htm"], "keywords": ["<!DOCTYPE", "<html", "<body"]},
    "css": {"extensions": [".css", ".scss"], "keywords": ["{", "@media", ":" ]},
    "java": {"extensions": [".java"], "keywords": ["public class", "public static void main"]},
    "cpp": {"extensions": [".cpp", ".h"], "keywords": ["#include", "int main", "std::"]},
    "sql": {"extensions": [".sql"], "keywords": ["SELECT", "FROM", "CREATE TABLE"]},
}


def _detect_language(req: GradeRequest) -> tuple[str, int]:
    code = req.student_code or ""
    fname = (req.file_name or "").lower()
    best_lang, best_score = "unknown", 0
    for lang, sig in LANGUAGE_PATTERNS.items():
        score = 0
        if any(fname.endswith(e) for e in sig["extensions"]):
            score += 4
        score += sum(2 for kw in sig["keywords"] if kw in code)
        if score > best_score:
            best_lang, best_score = lang, score
    return best_lang, best_score


def _score_compatibility(req: GradeRequest, total: int) -> tuple[int, list[str], list[str]]:
    max_p = int(total * 0.15)
    code = req.student_code or ""
    fname = (req.file_name or "").lower()
    ww, issues = [], []

    lang, conf = _detect_language(req)
    has_ext = any(fname.endswith(e) for sig in LANGUAGE_PATTERNS.values() for e in sig["extensions"])

    if lang != "unknown":
        ww.append(f"Language detected as {lang} (confidence {conf})")
    else:
        issues.append("Could not determine programming language from file extension or code patterns")

    if has_ext:
        ww.append(f"File extension '{fname.split('.')[-1]}' matches detected language")
    else:
        if fname:
            issues.append(f"File extension '.{fname.split(".")[-1] if "." in fname else "?"}' is not standard — rename for proper language support")

    syntax_ok = True
    if lang == "python":
        try:
            ast.parse(code)
            ww.append("Python syntax valid — no parsing errors")
        except SyntaxError as e:
            issues.append(f"Python syntax error at line {e.lineno}: {e.msg}")
            syntax_ok = False
    elif lang in ("javascript", "typescript", "react"):
        lines = code.splitlines()
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.endswith("{"):
                continue
            if stripped.startswith(("//", "/*")):
                continue
            if not stripped:
                continue
        ww.append("Syntax patterns appear valid")

    score = max_p
    deduction = 0
    has_ext_detected = lang != "unknown" and has_ext
    if not has_ext_detected:
        deduction += max_p * 0.4
    if not syntax_ok:
        deduction += max_p * 0.6
    score = max(0, int(max_p - deduction))
    return score, ww, issues


def _score_correctness(req: GradeRequest, total: int) -> tuple[int, list[str], list[str]]:
    max_p = int(total * 0.25)
    code = req.student_code or ""
    lang, _ = _detect_language(req)
    exp_out = req.expected_output or ""
    sample = req.sample_output or ""
    ww, issues = [], []

    checks = 0
    passed = 0

    # input handling
    if ("input(" in code) or ("prompt(" in code):
        checks += 1
        if lang == "python" and "int(" in code or "float(" in code:
            passed += 1
            ww.append("Input correctly converted with int()/float()")
        elif lang in ("javascript", "typescript") and ("Number(" in code or "parseInt" in code):
            passed += 1
            ww.append("Input correctly converted with Number()/parseInt()")
        else:
            issues.append("Input not converted to number type — will cause type errors in calculations")

    # output
    has_output = bool(re.search(r'print\s*\(|console\.log|System\.out|document\.write', code))
    if has_output:
        checks += 1
        passed += 1
        ww.append("Output statements present (print/console.log)")
    else:
        checks += 1
        issues.append("No output statements found — program cannot display results")

    # error handling
    has_error_handling = bool(re.search(r'try|except|catch|if\s+__name__\s*==', code))
    if has_error_handling:
        checks += 1
        passed += 1
        ww.append("Error handling patterns detected (try/except/catch)")
    elif "input(" in code or "prompt(" in code:
        checks += 1
        issues.append("No error handling for user input — use try/except or try/catch")

    # logic — division by zero
    if lang == "python":
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Constant) and child.value == 0:
                            issues.append("Division by zero detected — will crash at runtime")
                            break
        except SyntaxError:
            pass

    # output comparison
    if sample:
        checks += 1
        sam_clean = sample.lower().strip()
        if sam_clean in code.lower():
            passed += 1
            ww.append("Code includes expected output format")
        else:
            issues.append(f"Expected output '{sample[:50]}...' not found in code — verify output format")

    score = int(max_p * (passed / max(checks, 1))) if checks else max_p
    return score, ww, issues


def _score_file_structure(req: GradeRequest, total: int) -> tuple[int, list[str], list[str]]:
    max_p = int(total * 0.10)
    fname = req.file_name or ""
    folder = req.folder_structure or ""
    instructions = req.assignment_instructions or ""
    rubric = req.rubric or ""
    ww, issues = [], []

    if not fname:
        issues.append("No filename provided — cannot validate naming conventions")
        return max(0, int(max_p * 0.3)), ww, issues

    if " " in fname:
        issues.append(f"Filename '{fname}' contains spaces — use underscores or hyphens instead")
    else:
        ww.append(f"Filename '{fname}' has no spaces — good naming practice")

    if fname.startswith("."):
        issues.append(f"'{fname}' is a hidden file — rename to a meaningful name")
    else:
        ww.append("Filename is not hidden (does not start with dot)")

    bad_chars = set("!@#$%^&*()+={}[]|\\:;\"'<>,?/~`")
    special = [c for c in fname if c in bad_chars]
    if special:
        issues.append(f"Special characters {set(special)} in filename — use only letters, numbers, underscore, hyphen")
    else:
        ww.append("No special characters in filename")

    expected = re.findall(r"(\w+\.\w+)", instructions + "\n" + rubric)
    expected = list(set(f.lower() for f in expected if len(f) > 3))
    if expected:
        missing = [e for e in expected if e not in (fname.lower() + "\n" + folder.lower())]
        if missing:
            issues.append(f"Expected files not found in submission: {', '.join(missing[:5])}")
        else:
            ww.append(f"All expected files ({len(expected)}) are present")

    score = max_p
    deductions = 0
    if " " in fname:
        deductions += max_p * 0.2
    if fname.startswith("."):
        deductions += max_p * 0.2
    if special:
        deductions += max_p * 0.2
    if expected and missing:
        deductions += max_p * 0.3
    if not folder:
        deductions += max_p * 0.1
    score = max(0, int(max_p - deductions))
    return score, ww, issues


def _score_requirements(req: GradeRequest, total: int) -> tuple[int, list[str], list[str]]:
    max_p = int(total * 0.30)
    code = req.student_code or ""
    instructions = req.assignment_instructions or ""
    rubric = req.rubric or ""
    ww, issues = [], []

    all_text = instructions + "\n" + rubric
    req_lines = [l.strip() for l in all_text.splitlines() if l.strip()]
    req_lines = [
        l for l in req_lines
        if any(kw in l.lower() for kw in [
            "must", "should", "require", "need", "implement",
            "create", "write", "add", "include", "define", "use", "function",
            "display", "show", "print", "return", "calculate", "convert",
            "validate", "check", "handle", "format",
        ])
    ]
    if not req_lines:
        req_lines = [l for l in all_text.splitlines() if l.strip()][:10]

    code_lower = code.lower()
    met, partial, missed = [], [], []
    for req_line in req_lines:
        words = [w.strip(".,;:!?()[]{}\"'") for w in req_line.lower().split() if len(w) > 3]
        if not words:
            continue
        matched = sum(1 for w in words if w in code_lower)
        ratio = matched / len(words)
        if ratio >= 0.6:
            met.append(req_line)
        elif ratio >= 0.3:
            partial.append(req_line)
        else:
            missed.append(req_line)

    if met:
        ww.append(f"{len(met)} requirement(s) fully met")
    if partial:
        issues.append(f"{len(partial)} requirement(s) partially met — needs improvement")
    if missed:
        issues.append(f"{len(missed)} requirement(s) not evident in code")

    ratio = (len(met) + len(partial) * 0.5) / max(len(req_lines), 1)
    score = int(max_p * min(ratio, 1.0))
    return score, ww, issues


def _score_code_quality(req: GradeRequest, total: int) -> tuple[int, list[str], list[str]]:
    max_p = int(total * 0.10)
    code = req.student_code or ""
    lang, _ = _detect_language(req)
    ww, issues = [], []

    checks = 0
    passed = 0

    has_functions = bool(re.search(r'def \w+\s*\(|function \w+\s*\(|const \w+\s*=\s*\(?\s*\)?\s*=>', code))
    if has_functions:
        checks += 1
        passed += 1
        ww.append("Functions defined — good code organization")

    has_classes = bool(re.search(r'class \w+', code))
    if has_classes:
        checks += 1
        passed += 1
        ww.append("Classes defined — object-oriented structure")
    else:
        checks += 1

    has_main = bool(re.search(r'if\s+__name__\s*==|def main\(|if __name__', code))
    if lang == "python" and has_main:
        checks += 1
        passed += 1
        ww.append("main() or __name__ guard present — proper entry point")

    has_doc = bool(re.search(r'"""|\'\'\'|//.*doc|/\*\*|#.*docstring', code))
    if has_doc:
        checks += 1
        passed += 1
        ww.append("Documentation/docstrings present")
    else:
        if has_functions:
            checks += 1
            issues.append('No docstrings in functions - add triple-quote docstrings to explain purpose')

    naming_good = True
    if lang == "python" and has_functions:
        func_names = re.findall(r'def (\w+)\s*\(', code)
        for fn in func_names:
            if fn != fn.lower():
                naming_good = False
                issues.append(f"Function '{fn}' uses mixed case — Python uses snake_case")
                break
    if naming_good and has_functions:
        ww.append("Naming follows language conventions")

    score = int(max_p * (passed / max(checks, 1))) if checks else max_p
    return score, ww, issues


def _score_cleanliness(req: GradeRequest, total: int) -> tuple[int, list[str], list[str]]:
    max_p = int(total * 0.10)
    code = req.student_code or ""
    ww, issues = [], []

    lines = code.splitlines()
    if not lines:
        issues.append("No code to evaluate")
        return 0, ww, issues

    indent_ok = True
    for i, line in enumerate(lines, 1):
        if line.strip() and line[0] == " ":
            spaces = len(line) - len(line.lstrip())
            if spaces % 4 != 0 and spaces % 2 != 0:
                indent_ok = False
                issues.append(f"Line {i}: inconsistent indentation (not multiple of 2 or 4 spaces)")
                break
    if indent_ok:
        ww.append("Consistent indentation throughout")

    empty_lines = sum(1 for l in lines if not l.strip())
    total_lines = len(lines)
    empty_ratio = empty_lines / total_lines if total_lines else 0
    if empty_ratio > 0.4:
        issues.append(f"Excessive blank lines ({empty_lines}/{total_lines}) — reduce whitespace")
    elif empty_ratio > 0.1:
        ww.append("Good use of blank lines for readability")

    line_lengths = [len(l) for l in lines if l.strip()]
    long_lines = sum(1 for ll in line_lengths if ll > 100)
    if long_lines > 0:
        issues.append(f"{long_lines} line(s) exceed 100 characters — break into shorter lines")

    if not any(not l.strip() for l in lines):
        ww.append("Concise code with no wasted lines")

    score = max_p
    deductions = 0
    if not indent_ok:
        deductions += max_p * 0.4
    if empty_ratio > 0.4:
        deductions += max_p * 0.3
    if long_lines > 0:
        deductions += max_p * 0.3
    score = max(0, int(max_p - deductions))
    return score, ww, issues


def build_grade_response(req: GradeRequest) -> GradeResponse:
    total = req.total_marks or 100

    compat_score, compat_ww, compat_issues = _score_compatibility(req, total)
    correct_score, correct_ww, correct_issues = _score_correctness(req, total)
    file_score, file_ww, file_issues = _score_file_structure(req, total)
    req_score, req_ww, req_issues = _score_requirements(req, total)
    quality_score, quality_ww, quality_issues = _score_code_quality(req, total)
    clean_score, clean_ww, clean_issues = _score_cleanliness(req, total)

    final_score = compat_score + correct_score + file_score + req_score + quality_score + clean_score
    final_score = max(0, min(final_score, total))

    all_ww = compat_ww + correct_ww + file_ww + req_ww + quality_ww + clean_ww
    all_issues = compat_issues + correct_issues + file_issues + req_issues + quality_issues + clean_issues
    all_improvements = [i for i in all_issues if i not in all_ww]

    verdict_levels = [
        (90, "Excellent work! Bohot umda code hai!"),
        (75, "Good job! Aap ne accha code likha hai."),
        (60, "Decent effort! Mazeed behtari ki gunejaish hai."),
        (40, "Needs improvement. Practice karte rahein!"),
        (0, "Significant work needed. Dobara koshish karein."),
    ]
    verdict = next(v for threshold, v in verdict_levels if final_score >= threshold)

    explanation_parts = []
    categories = [
        ("Compatibility", compat_score, int(total * 0.15)),
        ("Correctness", correct_score, int(total * 0.25)),
        ("File Structure", file_score, int(total * 0.10)),
        ("Requirements", req_score, int(total * 0.30)),
        ("Code Quality", quality_score, int(total * 0.10)),
        ("Cleanliness", clean_score, int(total * 0.10)),
    ]
    for name, scored, outof in categories:
        pct = (scored / outof * 100) if outof else 0
        if pct >= 80:
            explanation_parts.append(f"{name}: {scored}/{outof} — strong")
        elif pct >= 50:
            explanation_parts.append(f"{name}: {scored}/{outof} — average")
        else:
            explanation_parts.append(f"{name}: {scored}/{outof} — needs work")
    explanation = " | ".join(explanation_parts)

    corrected_code = _generate_corrected_code(req, all_issues)

    major_issues = all_issues[:6]

    suggested_improvements = sorted(set(
        i.replace("[SYNTAX] ", "").replace("[LOGIC] ", "").replace("[FILE] ", "").replace("[MISSING] ", "").replace("[STRUCTURE] ", "")
        for i in all_issues
    ))[:6]

    return GradeResponse(
        score=f"{final_score}/{total}",
        verdict=verdict,
        what_went_well=all_ww[:8],
        major_issues=major_issues,
        explanation=explanation,
        suggested_improvements=suggested_improvements,
        corrected_code=corrected_code,
    )


def _generate_corrected_code(req: GradeRequest, issues: list[str]) -> str:
    code = req.student_code or ""
    if not code.strip():
        return ""

    lang, _ = _detect_language(req)
    has_input = "input(" in code or "prompt(" in code
    missing_conversion = any("not converted" in i.lower() for i in issues)
    missing_error = any("error handling" in i.lower() for i in issues)
    missing_docstring = any("docstring" in i.lower() for i in issues)

    corrected = code
    if lang == "python":
        lines = code.splitlines()
        output_lines = []
        tq = chr(34) * 3
        for line in lines:
            trimmed = line.strip()
            if missing_conversion and trimmed.startswith("input("):
                indent = line[:len(line) - len(line.lstrip())]
                var_match = re.match(r'(\w+)\s*=\s*input\(', trimmed)
                if var_match:
                    var = var_match.group(1)
                    output_lines.append(indent + "try:")
                    output_lines.append(indent + "    " + var + " = float(input(...))")
                    if missing_error:
                        output_lines.append(indent + "except ValueError:")
                        output_lines.append(indent + "    print('Invalid input! Please enter a number.')")
                        output_lines.append(indent + "    return")
                    else:
                        output_lines.append(indent + "    " + var + " = float(input(...))")
                else:
                    output_lines.append(line)
            elif missing_docstring and trimmed.startswith("def "):
                indent = line[:len(line) - len(line.lstrip())]
                fn_name = re.match(r'def (\w+)\s*\(', trimmed)
                if fn_name:
                    output_lines.append(line)
                    doc_text = fn_name.group(1).replace("_", " ").title()
                    output_lines.append(indent + "    " + tq + doc_text + "." + tq)
                else:
                    output_lines.append(line)
            else:
                output_lines.append(line)
        corrected = "\n".join(output_lines)

    return corrected
