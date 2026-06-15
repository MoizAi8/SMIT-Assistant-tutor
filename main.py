import asyncio
import sys
from pathlib import Path

from agents import Runner, set_default_openai_key

from src.config import OPENAI_API_KEY, require_api_key
from src.models import TeachingContext
from src.agents.teaching_assistant import teaching_assistant_agent
from src.agents.chatbot import run_chatbot_session


def read_file(path: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        print(f"Error: File not found: {path}")
        sys.exit(1)
    return file_path.read_text(encoding="utf-8")


def parse_cli_args() -> dict:
    args = {
        "assignment_title": "",
        "assignment_instructions": "",
        "rubric": "",
        "total_marks": 100,
        "student_code": "",
        "file_name": "",
        "folder_structure": "",
        "expected_output": "",
        "sample_output": "",
        "previous_feedback": "",
        "class_notes": "",
        "common_mistakes": "",
        "student_name": "Student",
    }

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.startswith("--"):
            key = arg[2:].replace("-", "_")
            i += 1
            if i < len(sys.argv) and not sys.argv[i].startswith("--"):
                if key == "total_marks":
                    args[key] = int(sys.argv[i])
                elif key in ("student_code", "assignment_instructions", "rubric",
                             "expected_output", "sample_output", "previous_feedback",
                             "class_notes", "common_mistakes"):
                    args[key] = read_file(sys.argv[i])
                else:
                    args[key] = sys.argv[i]
            i += 1
        else:
            i += 1

    return args


def print_usage():
    print("=" * 60)
    print("  AI Teaching Assistant — Code Grader + Chatbot")
    print("=" * 60)
    print()
    print("Usage:")
    print("  python main.py [options]")
    print()
    print("Required options:")
    print("  --assignment-title <title>")
    print("  --assignment-instructions <file>")
    print("  --rubric <file>")
    print("  --student-code <file>")
    print()
    print("Optional options:")
    print("  --total-marks <number>             (default: 100)")
    print("  --file-name <filename>")
    print("  --folder-structure <text>")
    print("  --expected-output <file>")
    print("  --sample-output <file>")
    print("  --previous-feedback <file>")
    print("  --class-notes <file>")
    print("  --common-mistakes <file>")
    print("  --student-name <name>              (default: Student)")
    print()
    print("Example:")
    print('  python main.py ^')
    print('    --assignment-title "Temperature Converter" ^')
    print('    --assignment-instructions examples/sample_assignment.md ^')
    print('    --rubric examples/sample_rubric.md ^')
    print('    --student-code examples/sample_submission.py ^')
    print('    --total-marks 100 ^')
    print('    --file-name sample_submission.py ^')
    print('    --expected-output examples/sample_output.txt ^')
    print('    --student-name "Ali"')
    print()


async def main():
    set_default_openai_key(OPENAI_API_KEY)

    if len(sys.argv) < 2 or "--help" in sys.argv or "-h" in sys.argv:
        print_usage()
        sys.exit(1)

    args = parse_cli_args()

    if not args["assignment_instructions"] or not args["rubric"] or not args["student_code"]:
        print("Error: --assignment-instructions, --rubric, and --student-code are required.")
        print()
        print_usage()
        sys.exit(1)

    require_api_key()

    context = TeachingContext(
        assignment_title=args["assignment_title"],
        assignment_instructions=args["assignment_instructions"],
        rubric=args["rubric"],
        total_marks=args["total_marks"],
        student_code=args["student_code"],
        file_name=args["file_name"],
        folder_structure=args["folder_structure"],
        expected_output=args["expected_output"],
        sample_output=args["sample_output"],
        previous_feedback=args["previous_feedback"],
        class_notes=args["class_notes"],
        common_mistakes=args["common_mistakes"],
        student_name=args["student_name"],
    )

    print("=" * 60)
    title = context.assignment_title or "Code Submission"
    print(f"  Grading: {title}")
    print(f"  Student: {context.student_name}")
    print("=" * 60)
    print()

    user_message = (
        f"Please grade this submission.\n\n"
        f"Assignment Title: {context.assignment_title}\n"
        f"Total Marks: {context.total_marks}\n\n"
        f"--- STUDENT CODE ---\n{context.student_code}\n\n"
        f"--- FILE NAME ---\n{context.file_name}\n\n"
        f"--- FOLDER STRUCTURE ---\n{context.folder_structure}\n\n"
        f"--- ASSIGNMENT INSTRUCTIONS ---\n{context.assignment_instructions}\n\n"
        f"--- RUBRIC ---\n{context.rubric}\n\n"
        f"--- EXPECTED OUTPUT ---\n{context.expected_output}\n\n"
        f"--- SAMPLE OUTPUT ---\n{context.sample_output}\n\n"
        f"--- PREVIOUS FEEDBACK ---\n{context.previous_feedback}\n\n"
        f"--- CLASS NOTES ---\n{context.class_notes}\n\n"
        f"--- COMMON MISTAKES ---\n{context.common_mistakes}\n\n"
        f"Evaluate thoroughly and return the exact output format."
    )

    print("Evaluating submission...")
    print()

    result = await Runner.run(teaching_assistant_agent, user_message, context=context)
    grade = result.final_output

    print("\n" + "=" * 60)
    print("  GRADING RESULT")
    print("=" * 60)
    print()

    print(f"Score: {grade.score}")
    print(f"Verdict: {grade.verdict}")
    print()
    print("--- What Went Well ---")
    for item in grade.what_went_well:
        print(f"  + {item}")
    print()
    print("--- Major Issues ---")
    for issue in grade.major_issues:
        print(f"  ! {issue}")
    print()
    print("--- Explanation ---")
    print(f"  {grade.explanation}")
    print()
    print("--- Suggested Improvements ---")
    for imp in grade.suggested_improvements:
        print(f"  -> {imp}")
    print()
    print("--- Corrected Code ---")
    print(grade.corrected_code)

    await run_chatbot_session(grade)


if __name__ == "__main__":
    asyncio.run(main())
