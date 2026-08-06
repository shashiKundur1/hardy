import sys
from pathlib import Path

WEB_FRAMEWORKS = ("fastapi", "flask", "django")
LLM_CLIENTS = ("openai", "anthropic", "litellm", "google-generativeai")


def main() -> int:
    text = Path("requirements.txt").read_text().lower()
    missing = []
    if not any(name in text for name in WEB_FRAMEWORKS):
        missing.append("a web framework")
    if not any(name in text for name in LLM_CLIENTS):
        missing.append("an LLM client")
    if missing:
        print(f"requirements.txt is missing {' and '.join(missing)}.")
        print("The organiser's `requirements` check fails without both, which voids the entry.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
