import asyncio
import compileall
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SKIP = {".venv", "__pycache__", ".git", "node_modules"}

MANIFESTS = ("requirements.txt", "pyproject.toml", "Pipfile")
WEB_FRAMEWORKS = ("fastapi", "flask", "django")
LLM_CLIENTS = ("openai", "anthropic", "litellm", "google-generativeai")


def tracked_python() -> list[Path]:
    return [path for path in ROOT.rglob("*.py") if not SKIP & set(path.relative_to(ROOT).parts)]


def compiles() -> tuple[bool, str]:
    targets = [ROOT / "src", ROOT / "scripts", ROOT / "tests"]
    ok = all(compileall.compile_dir(str(target), quiet=2) for target in targets)
    return ok, f"all {len(tracked_python())} files compile cleanly"


def requirements() -> tuple[bool, str]:
    found = [name for name in MANIFESTS if (ROOT / name).exists()]
    if not found:
        return False, f"no dependency manifest: expected one of {', '.join(MANIFESTS)}"
    text = "".join((ROOT / name).read_text().lower() for name in found)
    web = next((name for name in WEB_FRAMEWORKS if name in text), None)
    llm = next((name for name in LLM_CLIENTS if name in text), None)
    if web and llm:
        return True, f"web framework ({web}) + LLM client ({llm}) in {', '.join(found)}"
    missing = "web framework" if not web else "LLM client"
    return False, f"{' and '.join(found)} declare no {missing}"


def mesh_used() -> tuple[bool, str]:
    hits = sorted(
        path.name for path in tracked_python() if "mesh" in path.read_text(errors="ignore").lower()
    )
    if not hits:
        return False, "no Mesh reference in any tracked .py file"
    return True, "Mesh API referenced in: " + ", ".join(hits[:6])


def mesh_key() -> tuple[bool, str]:
    async def call() -> str:
        from src.integrations import mesh

        completion = await mesh.chat(
            [{"role": "user", "content": "Reply with exactly: ok"}], max_tokens=5
        )
        return completion.content

    try:
        content = asyncio.run(call())
    except Exception as error:
        return False, f"Mesh API key rejected: {type(error).__name__}: {error}"
    return bool(content.strip()), "Mesh API key is valid"


CHECKS = (
    ("compiles", compiles),
    ("requirements", requirements),
    ("mesh_used", mesh_used),
    ("mesh_key", mesh_key),
)


def main() -> int:
    passed = 0
    for name, check in CHECKS:
        try:
            ok, detail = check()
        except Exception as error:
            ok, detail = False, f"{type(error).__name__}: {error}"
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
        passed += ok
    print(f"        {passed}/{len(CHECKS)} critical checks passed")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
