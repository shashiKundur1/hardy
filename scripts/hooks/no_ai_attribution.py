import re
import sys
from pathlib import Path

TRAILER = re.compile(r"^\s*co-authored-by:", re.IGNORECASE | re.MULTILINE)
ASSISTED = re.compile(
    r"\b(generated with|written by an? (ai|assistant|agent)|ai-(generated|assisted))\b",
    re.IGNORECASE,
)
DIARY = re.compile(r"^\s*(day\s*\d+\b|wip\b|part\s*\d+\b|status\s*update\b)", re.IGNORECASE)


def main() -> int:
    message = Path(sys.argv[1]).read_text()

    if TRAILER.search(message):
        print("Commit message carries a Co-Authored-By trailer.")
        print("Rule 1: every commit is Shashi's alone. No second author, ever.")
        return 1

    if ASSISTED.search(message):
        print("Commit message credits a tool for authorship.")
        print("Rule 1: no assistance attribution anywhere in git history.")
        return 1

    lines = message.splitlines()
    if lines and DIARY.match(lines[0]):
        print(f"Commit message reads like a diary entry: {lines[0]!r}")
        print("Rule 1: commit messages describe the change, never the process.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
