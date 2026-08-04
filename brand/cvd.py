#!/usr/bin/env python3
import itertools
import sys

LMS_FROM_RGB = (
    (0.31399022, 0.63951294, 0.04649755),
    (0.15537241, 0.75789446, 0.08670142),
    (0.01775239, 0.10944209, 0.87256922),
)
RGB_FROM_LMS = (
    (5.47221206, -4.64196010, 0.16963708),
    (-1.12524190, 2.29317094, -0.16789520),
    (0.02980165, -0.19318073, 1.16364789),
)
SIM = {
    "protanopia": ((0.0, 1.05118294, -0.05116099), (0, 1, 0), (0, 0, 1)),
    "deuteranopia": ((1, 0, 0), (0.9513092, 0.0, 0.04264542), (0, 0, 1)),
    "tritanopia": ((1, 0, 0), (0, 1, 0), (-0.86744736, 1.86727089, 0.0)),
}


def to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def to_srgb(c):
    c = max(0.0, min(1.0, c))
    return c * 12.92 if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def mul(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def hex_to_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


def rgb_to_hex(rgb):
    return "#%02X%02X%02X" % tuple(round(max(0, min(1, c)) * 255) for c in rgb)


def simulate(hex_colour, kind):
    lin = tuple(to_linear(c) for c in hex_to_rgb(hex_colour))
    lms = mul(LMS_FROM_RGB, lin)
    lms = mul(SIM[kind], lms)
    return rgb_to_hex(tuple(to_srgb(c) for c in mul(RGB_FROM_LMS, lms)))


def luminance(hex_colour):
    r, g, b = (to_linear(c) for c in hex_to_rgb(hex_colour))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)))
    return (lb + 0.05) / (la + 0.05)


def distance(a, b):
    ra, ga, ba = (c * 255 for c in hex_to_rgb(a))
    rb, gb, bb = (c * 255 for c in hex_to_rgb(b))
    rm = (ra + rb) / 2 / 255
    dr, dg, db = ra - rb, ga - gb, ba - bb
    return (((2 + rm) * dr * dr) + (4 * dg * dg) + ((3 - rm) * db * db)) ** 0.5


UI_PAIRS = [
    ("#FFFFFF", "#0B0B0C", 4.5, "heading on page"),
    ("#E6E9ED", "#0B0B0C", 4.5, "body on page"),
    ("#E6E9ED", "#16171A", 4.5, "body on surface"),
    ("#A8AEB8", "#0B0B0C", 4.5, "secondary on page"),
    ("#8B929C", "#0B0B0C", 3.0, "muted on page"),
    ("#FFB302", "#0B0B0C", 4.5, "amber accent on page"),
    ("#FFB302", "#16171A", 4.5, "amber on surface"),
    ("#4DA3FF", "#0B0B0C", 4.5, "signal blue on page"),
    ("#0B0B0C", "#FFB302", 4.5, "ink on amber button"),
]

SEMANTIC = {
    "amber": "#FFB302",
    "signal": "#4DA3FF",
    "surface": "#16171A",
    "muted": "#8B929C",
    "body": "#E6E9ED",
}

MAP_PALETTE = {
    "browser": "#56B4E9",
    "ingest": "#F0E442",
    "trigger": "#CC79A7",
    "agent": "#6BE1A0",
    "retrieval": "#7F5FFF",
    "store": "#D55E00",
    "mesh": "#FFB302",
}

MIN_DISTANCE = 90


def main() -> int:
    failures = []

    print("=" * 74)
    print("1. UI CONTRAST — WCAG AA, normal vision")
    print("=" * 74)
    for fg, bg, floor, label in UI_PAIRS:
        r = contrast(fg, bg)
        ok = r >= floor
        if not ok:
            failures.append(f"contrast {label}: {r:.2f}:1 < {floor}")
        print(f"{'PASS' if ok else 'FAIL'}  {r:5.2f}:1 (min {floor})  {fg} on {bg}  {label}")

    print()
    print("=" * 74)
    print("2. UI CONTRAST HOLDS UNDER COLOUR BLINDNESS")
    print("=" * 74)
    for kind in SIM:
        print(f"\n  -- {kind} --")
        for fg, bg, floor, label in UI_PAIRS:
            r = contrast(simulate(fg, kind), simulate(bg, kind))
            ok = r >= floor
            if not ok:
                failures.append(f"{kind} contrast {label}: {r:.2f}:1 < {floor}")
            print(f"  {'PASS' if ok else 'FAIL'}  {r:5.2f}:1  {label}")

    print()
    print("=" * 74)
    print("3. SEMANTIC COLOURS STAY DISTINCT FROM EACH OTHER")
    print("=" * 74)
    for kind in SIM:
        print(f"\n  -- {kind} --")
        for (n1, c1), (n2, c2) in itertools.combinations(SEMANTIC.items(), 2):
            d = distance(simulate(c1, kind), simulate(c2, kind))
            ok = d >= MIN_DISTANCE
            if not ok:
                failures.append(f"{kind}: {n1} vs {n2} collapse (d={d:.0f})")
            print(f"  {'PASS' if ok else 'FAIL'}  d={d:6.1f}  {n1:8} vs {n2:8}"
                  f"  {simulate(c1, kind)} / {simulate(c2, kind)}")

    print()
    print("=" * 74)
    print("4. PROCESS MAP LANES STAY DISTINCT (Okabe-Ito derived)")
    print("=" * 74)
    for kind in SIM:
        worst = None
        for (n1, c1), (n2, c2) in itertools.combinations(MAP_PALETTE.items(), 2):
            d = distance(simulate(c1, kind), simulate(c2, kind))
            if worst is None or d < worst[0]:
                worst = (d, n1, n2)
        ok = worst[0] >= MIN_DISTANCE
        if not ok:
            failures.append(f"{kind} map: {worst[1]} vs {worst[2]} collapse (d={worst[0]:.0f})")
        print(f"  {'PASS' if ok else 'FAIL'}  {kind:13} closest pair: "
              f"{worst[1]} vs {worst[2]} at d={worst[0]:.1f} (min {MIN_DISTANCE})")

    print()
    if failures:
        print(f"{len(failures)} FAILURE(S):")
        for f in failures:
            print("  -", f)
        return 1
    print("ALL CHECKS PASS — palette is legible with normal vision and all three "
          "dichromacies.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
