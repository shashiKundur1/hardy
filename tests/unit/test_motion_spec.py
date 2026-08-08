import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
STYLE = (ROOT / "src" / "static" / "style.css").read_text()
TOKENS = (ROOT / "brand" / "tokens.css").read_text()

LAYOUT_PROPERTIES = ("width", "height", "margin", "padding", "top", "left", "right", "bottom")


def test_no_duration_or_easing_is_written_at_a_call_site():
    stray = re.findall(r"[0-9]+ms|cubic-bezier", STYLE)
    assert not stray, f"style.css must use tokens, found {stray}"


def test_every_motion_token_is_defined():
    for token in (
        "--ease",
        "--ease-enter",
        "--ease-exit",
        "--duration-fast",
        "--duration",
        "--duration-slow",
        "--lift",
    ):
        assert f"{token}:" in TOKENS, token


def test_reduced_motion_zeroes_every_duration_at_the_token_level():
    reduced = TOKENS.split("prefers-reduced-motion")[1]
    for token in ("--duration-fast", "--duration", "--duration-slow"):
        assert re.search(rf"{token}:\s*0ms", reduced), token
    assert re.search(r"--lift:\s*0px", reduced)


@pytest.mark.parametrize("prop", LAYOUT_PROPERTIES)
def test_no_layout_property_is_ever_transitioned(prop):
    for block in re.findall(r"transition:\s*([^;]+);", STYLE):
        assert not re.search(rf"\b{prop}\s+[0-9v]", block), f"{prop} animated in: {block}"


def test_the_motion_spec_exists_and_cites_its_numbers():
    spec = (ROOT / "brand" / "MOTION.md").read_text()
    assert "nngroup.com" in spec
    assert "m3.material.io" in spec
    assert "prefers-reduced-motion" in spec
