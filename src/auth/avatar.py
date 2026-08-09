import hashlib
import math
from xml.sax.saxutils import escape

INKS = (
    "var(--amber)",
    "var(--signal)",
    "var(--state-ok)",
    "var(--steel-200)",
    "var(--amber-deep)",
    "var(--lane-retrieval)",
)
SPOKE_COUNTS = (6, 8, 10, 12)
RING_COUNTS = (1, 2, 3)
RIVET_COUNTS = (0, 4, 6, 8)
CENTRE_FORMS = ("hex", "disc", "square", "diamond")

CENTRE = 24.0
RING_RADII = (13.5, 17.0, 20.0)
SPOKE_INNER = 19.0
SPOKE_OUTER = 22.0
RIVET_ORBIT = 15.5
CORE_RADIUS = 8.6


def _digits(seed: str) -> bytes:
    return hashlib.sha256(seed.encode()).digest()


def _polygon(sides: int, radius: float, rotation: float) -> str:
    points = []
    for index in range(sides):
        angle = rotation + index * 2 * math.pi / sides
        x = CENTRE + radius * math.cos(angle)
        y = CENTRE + radius * math.sin(angle)
        points.append(f"{x:.2f},{y:.2f}")
    return " ".join(points)


def _core(form: str, ink: str) -> str:
    if form == "disc":
        return f'<circle cx="24" cy="24" r="{CORE_RADIUS}" fill="{ink}"/>'
    sides, rotation = {
        "hex": (6, 0.0),
        "square": (4, math.pi / 4),
        "diamond": (4, 0.0),
    }[form]
    return f'<polygon points="{_polygon(sides, CORE_RADIUS + 1.1, rotation)}" fill="{ink}"/>'


def traits(seed: str) -> dict:
    values = _digits(seed)
    return {
        "ink": INKS[values[0] % len(INKS)],
        "spokes": SPOKE_COUNTS[values[1] % len(SPOKE_COUNTS)],
        "rings": RING_COUNTS[values[2] % len(RING_COUNTS)],
        "rivets": RIVET_COUNTS[values[3] % len(RIVET_COUNTS)],
        "form": CENTRE_FORMS[values[4] % len(CENTRE_FORMS)],
        "twist": (values[5] % 12) * math.pi / 180,
    }


def markup(seed: str, name: str, size: int = 48) -> str:
    mark = traits(seed)
    ink = mark["ink"]
    parts = [
        '<circle cx="24" cy="24" r="23.4" fill="var(--surface-3)" '
        'stroke="var(--steel-700)" stroke-width="1.2"/>'
    ]
    for radius in RING_RADII[: mark["rings"]]:
        parts.append(
            f'<circle cx="24" cy="24" r="{radius}" fill="none" '
            f'stroke="var(--steel-700)" stroke-width="0.9"/>'
        )
    for index in range(mark["spokes"]):
        angle = mark["twist"] + index * 2 * math.pi / mark["spokes"]
        x1 = CENTRE + SPOKE_INNER * math.cos(angle)
        y1 = CENTRE + SPOKE_INNER * math.sin(angle)
        x2 = CENTRE + SPOKE_OUTER * math.cos(angle)
        y2 = CENTRE + SPOKE_OUTER * math.sin(angle)
        parts.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="var(--steel-600)" stroke-width="1.6" stroke-linecap="round"/>'
        )
    for index in range(mark["rivets"]):
        angle = math.pi / 4 + index * 2 * math.pi / mark["rivets"]
        x = CENTRE + RIVET_ORBIT * math.cos(angle)
        y = CENTRE + RIVET_ORBIT * math.sin(angle)
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="1.15" fill="var(--steel-600)"/>')
    parts.append(_core(mark["form"], ink))
    return (
        f'<svg class="avatar" viewBox="0 0 48 48" width="{size}" height="{size}" '
        f'role="img" aria-label="{escape(name, {chr(34): "&quot;"})}" focusable="false">'
        f"<title>{escape(name)}</title>{''.join(parts)}</svg>"
    )


def for_user(user, size: int = 48) -> str:
    return markup(f"hardy:{user.id}:{user.email}", user.shown_name, size)
