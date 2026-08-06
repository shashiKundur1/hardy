import sys
from pathlib import Path

MANIFESTS = ("requirements.txt", "pyproject.toml", "Pipfile")
WEB_FRAMEWORKS = ("fastapi", "flask", "django")
LLM_CLIENTS = ("openai", "anthropic", "litellm", "google-generativeai")


def main() -> int:
    found = [name for name in MANIFESTS if Path(name).exists()]
    if not found:
        print(f"No dependency manifest. Expected one of: {', '.join(MANIFESTS)}.")
        return 1
    text = "".join(Path(name).read_text().lower() for name in found)
    missing = []
    if not any(name in text for name in WEB_FRAMEWORKS):
        missing.append("a web framework")
    if not any(name in text for name in LLM_CLIENTS):
        missing.append("an LLM client")
    if missing:
        print(f"{' and '.join(found)} declare no {' and no '.join(missing)}.")
        print("The organiser's `requirements` check fails without both, which voids the entry.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
