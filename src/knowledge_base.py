"""Knowledge base of common mistakes and class notes for feedback enrichment.
This is ONLY used to improve feedback quality — NEVER to invent or justify marks."""

COMMON_MISTAKES: dict[str, list[str]] = {
    "python": [
        "Forgetting colons (:) after if, else, elif, for, while, def",
        "Mixing tabs and spaces for indentation",
        "Using == instead of = for assignment (or vice versa)",
        "Forgetting to convert input() to int() or float()",
        "Variable name typos (using different names than defined)",
        "Not handling edge cases like zero division or empty input",
        "Missing return statement in functions",
        "Using global variables when parameters should be passed",
        "Off-by-one errors in loops and list indexing",
        "Not closing files after opening them",
    ],
    "functions": [
        "Defining function after calling it",
        "Not passing required arguments",
        "Modifying global variables inside functions without global keyword",
        "Function name doesn't match what it actually does",
    ],
    "loops": [
        "Infinite loops (forgetting to update loop variable)",
        "Using wrong range() values",
        "Looping over list while modifying it",
    ],
    "input_output": [
        "Not telling user what to enter (missing prompt message)",
        "Print format doesn't match expected output exactly",
        "Not handling invalid input types",
    ],
}

CLASS_NOTES: dict[str, list[str]] = {
    "variables": [
        "Variables store data in memory. Aap ek container samajh sakte hain.",
        "Use descriptive names: student_name not sn",
        "snake_case for variables in Python: my_variable not myVariable",
    ],
    "functions": [
        "Functions ko aap ek chhota sa program samajh sakte hain jo ek kaam karta hai",
        "def se function start hota hai, colon (:) zaroori hai",
        "return value bhejta hai wapas jahan se function call kiya tha",
    ],
    "conditionals": [
        "if, elif, else ke baad colon (:) lagana mat bhoolna",
        "Indentation (space) batati hai ke code if ke andar hai ya bahar",
        "Comparison == hai, assignment = hai — dono alag hain",
    ],
    "loops": [
        "for loop list ke har item ke liye ek baar chalta hai",
        "range(n) 0 se n-1 tak numbers deta hai",
        "while loop tab tak chalta hai jab tak condition True hai",
    ],
}


def get_hints_for_code(code: str) -> list[str]:
    """Return relevant common mistakes based on code content.
    Used ONLY for feedback enrichment, NEVER for marking."""
    hints = []
    code_lower = code.lower()

    if "python" in code_lower or "def " in code_lower:
        hints.extend(COMMON_MISTAKES["python"][:3])
    if "input(" in code_lower and "int(" not in code_lower and "float(" not in code_lower:
        hints.append("input() string return karta hai. Agar number chahiye to int() ya float() use karein")
    if "def " in code_lower:
        hints.extend(COMMON_MISTAKES["functions"][:2])
    if "for " in code_lower or "while " in code_lower:
        hints.extend(COMMON_MISTAKES["loops"][:1])
    if "print(" in code_lower:
        hints.extend(COMMON_MISTAKES["input_output"][:1])

    return hints


def get_notes_for_code(code: str) -> list[str]:
    """Return relevant class notes based on code content."""
    notes = []
    code_lower = code.lower()

    if "def " in code_lower:
        notes.extend(CLASS_NOTES["functions"])
    if "if " in code_lower or "elif" in code_lower or "else:" in code_lower:
        notes.extend(CLASS_NOTES["conditionals"])
    if "for " in code_lower or "while " in code_lower:
        notes.extend(CLASS_NOTES["loops"][:2])

    return notes
