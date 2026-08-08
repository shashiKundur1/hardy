import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STYLE = (ROOT / "src" / "static" / "style.css").read_text()
TOKENS = (ROOT / "brand" / "tokens.css").read_text()

TOO_DARK_FOR_TEXT = ("--steel-500", "--steel-600", "--steel-700")


def test_a_quiet_ink_token_exists_for_muted_text():
    assert "--ink-quiet:" in TOKENS


def test_no_style_paints_text_in_a_shade_that_fails_at_small_sizes():
    offenders = [
        token
        for token in TOO_DARK_FOR_TEXT
        if re.search(rf"^\s*color: var\({token}\);", STYLE, re.M)
    ]
    assert not offenders, (
        f"{offenders} measured below 4.5:1 at Hardy's text sizes; use --ink-quiet. "
        "Re-measure with brand/contrast-audit.js."
    )


def test_the_contrast_audit_is_committed_so_the_numbers_can_be_reproduced():
    script = (ROOT / "brand" / "contrast-audit.js").read_text()
    assert "hardyContrastAudit" in script
    assert "0.2126" in script


def test_muted_small_caps_resolve_to_the_quiet_ink():
    for style in ("eyebrow", "field__label", "stat__label", "browse__label"):
        block = re.search(rf"^\.{style} \{{[^}}]*\}}", STYLE, re.M)
        assert block, style
        assert "--steel-500" not in block.group(0)
