#!/usr/bin/env python3
import pathlib
import sys
from collections import deque

from PIL import Image, ImageFilter

DARK_MAX = 26
MIN_COMPONENT = 2000
FEATHER = 0.6
PAD = 12


def border_connected_dark(src):
    w, h = src.size
    px = src.load()
    dark = bytearray(w * h)
    for y in range(h):
        row = y * w
        for x in range(w):
            r, g, b = px[x, y]
            if 0.2126 * r + 0.7152 * g + 0.0722 * b <= DARK_MAX:
                dark[row + x] = 1

    mask = bytearray(w * h)
    queue = deque()
    for x in range(w):
        for idx in (x, (h - 1) * w + x):
            if dark[idx] and not mask[idx]:
                mask[idx] = 1
                queue.append(idx)
    for y in range(h):
        for idx in (y * w, y * w + w - 1):
            if dark[idx] and not mask[idx]:
                mask[idx] = 1
                queue.append(idx)

    while queue:
        idx = queue.popleft()
        cy, cx = divmod(idx, w)
        for nb, ok in ((idx - 1, cx > 0), (idx + 1, cx < w - 1),
                       (idx - w, cy > 0), (idx + w, cy < h - 1)):
            if ok and dark[nb] and not mask[nb]:
                mask[nb] = 1
                queue.append(nb)

    for start in range(w * h):
        if not dark[start] or mask[start]:
            continue
        component = []
        seen = deque([start])
        mask[start] = 2
        while seen:
            idx = seen.popleft()
            component.append(idx)
            cy, cx = divmod(idx, w)
            for nb, ok in ((idx - 1, cx > 0), (idx + 1, cx < w - 1),
                           (idx - w, cy > 0), (idx + w, cy < h - 1)):
                if ok and dark[nb] and not mask[nb]:
                    mask[nb] = 2
                    seen.append(nb)
        keep = len(component) >= MIN_COMPONENT
        for idx in component:
            mask[idx] = 1 if keep else 0

    return Image.frombytes("L", (w, h), bytes(bytearray(255 if v == 1 else 0 for v in mask)))


def cut(src_path, dst_path):
    src = Image.open(src_path).convert("RGB")
    w, h = src.size
    background = border_connected_dark(src)
    alpha = background.point(lambda v: 0 if v else 255)
    alpha = alpha.filter(ImageFilter.GaussianBlur(FEATHER))

    out = src.copy()
    out.putalpha(alpha)
    box = alpha.point(lambda v: 255 if v > 10 else 0).getbbox()
    if box:
        l, t, r, b = box
        out = out.crop((max(l - PAD, 0), max(t - PAD, 0),
                        min(r + PAD, w), min(b + PAD, h)))
    out.save(dst_path, optimize=True)
    hist = out.getchannel("A").histogram()
    n = out.width * out.height
    return out.size, 100 * hist[0] // n


if __name__ == "__main__":
    base = pathlib.Path(__file__).parent
    for name in sys.argv[1:]:
        size, clear = cut(base / "_work" / f"{name}.png", base / f"hardy-{name}.png")
        print(f"hardy-{name}.png  {size[0]}x{size[1]}  transparent={clear}%")
