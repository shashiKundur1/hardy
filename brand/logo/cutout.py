#!/usr/bin/env python3
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFilter

TOLERANCE = 26
EDGE_BLUR = 0.8
PAD = 20
MARKER = 7


def alpha_from_backdrop(src: pathlib.Path, dst: pathlib.Path, tol: int) -> tuple[int, int]:
    img = Image.open(src).convert("RGB")
    w, h = img.size
    probe = img.convert("L")

    for seed in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
                 (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)):
        ImageDraw.floodfill(probe, seed, MARKER, thresh=tol)

    alpha = probe.point(lambda v: 0 if v == MARKER else 255)
    alpha = alpha.filter(ImageFilter.GaussianBlur(EDGE_BLUR))

    out = img.copy()
    out.putalpha(alpha)

    box = alpha.point(lambda v: 255 if v > 8 else 0).getbbox()
    if box:
        l, t, r, b = box
        out = out.crop((max(l - PAD, 0), max(t - PAD, 0),
                        min(r + PAD, w), min(b + PAD, h)))
    out.save(dst, optimize=True)
    return out.size


if __name__ == "__main__":
    tol = int(sys.argv[1]) if sys.argv[1:] and sys.argv[1].isdigit() else TOLERANCE
    names = [a for a in sys.argv[1:] if not a.isdigit()]
    base = pathlib.Path(__file__).parent
    for name in names:
        w, h = alpha_from_backdrop(base / "_work" / f"{name}.png", base / f"hardy-{name}.png", tol)
        print(f"hardy-{name}.png  {w}x{h}  tol={tol}")
