#!/usr/bin/env python3
import pathlib
import re
import sys

TOKENS = pathlib.Path(__file__).parent / "tokens.css"

PAIRS = [
    ("--ink", "--paper", 4.5, "headings on page"),
    ("--ink", "--card", 4.5, "headings on card"),
    ("--ink-soft", "--paper", 4.5, "body on page"),
    ("--ink-soft", "--card", 4.5, "body on card"),
    ("--steel-deep", "--paper", 4.5, "tertiary on page"),
    ("--steel-deep", "--card", 4.5, "badge text on card"),
    ("--steel", "--paper", 4.5, "metadata on page"),
    ("--brass", "--paper", 4.5, "links on page"),
    ("--brass", "--card", 4.5, "cost-per-year on card"),
    ("--brass", "--brass-wash", 4.5, "continuity badge"),
    ("--state-error", "--paper", 4.5, "form error"),
    ("--state-ok", "--paper", 4.5, "in-sync state"),
    ("--brass", "--paper", 3.0, "focus ring on page"),
    ("--steel-light", "--paper", 3.0, "disabled on page"),
]


def parse_tokens(css: str) -> dict[str, str]:
    return dict(re.findall(r"(--[a-z-]+):\s*(#[0-9A-Fa-f]{6})\s*;", css))


def relative_luminance(hex_colour: str) -> float:
    r, g, b = (int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
    r, g, b = (c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg: str, bg: str) -> float:
    a, b = relative_luminance(fg), relative_luminance(bg)
    lo, hi = sorted((a, b))
    return (hi + 0.05) / (lo + 0.05)


def main() -> int:
    tokens = parse_tokens(TOKENS.read_text())
    failures = []
    for fg, bg, floor, label in PAIRS:
        r = ratio(tokens[fg], tokens[bg])
        ok = r >= floor
        if not ok:
            failures.append((label, fg, bg, r, floor))
        print(f"{'PASS' if ok else 'FAIL'}  {r:5.2f}:1  (min {floor})  {fg} on {bg}  — {label}")

    print()
    if failures:
        print(f"{len(failures)} FAILING PAIR(S):")
        for label, fg, bg, r, floor in failures:
            print(f"  {fg} on {bg} is {r:.2f}:1, needs {floor}:1 — {label}")
        return 1
    print(f"All {len(PAIRS)} pairs pass WCAG AA.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
