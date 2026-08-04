#!/usr/bin/env python3
import base64
import json
import os
import pathlib
import sys
import urllib.request

MODEL = "gemini-3-pro-image"
OUT = pathlib.Path(__file__).parent / "_work"

STEEL = (
    "Material: solid machined stainless steel with a brushed satin finish, covered in fine "
    "rigid scratches and micro-abrasions from real use. Reflective but not chrome — it catches "
    "light in soft broad highlights, not mirror glare. Every bevelled edge carries a hot amber "
    "rim-light that traces the outline like molten brass, bright enough to separate the metal "
    "from the darkness behind it. "
    "Lit dramatically from the upper left by a hard key light, with a strong amber rim light "
    "raking across the top and right edges, and deep shadow filling the lower left. "
    "Background: pure solid black, #000000, completely seamless and featureless, total void, "
    "no floor, no horizon line, no shadow cast onto the backdrop, no vignette, no grey. "
    "The metal must never blend into the background — the amber rim keeps every edge readable. "
    "Dark moody industrial product photography, sharp focus, high detail, 3D render quality."
)

VARIANTS = {
    "wordmark": (
        "A 3D-printed solid steel wordmark reading exactly \"HARDY\" in capital letters. "
        "The letterforms are bold, heavy, bulky and geometric — a wide industrial grotesque "
        "with thick even strokes, generous counters and slightly squared terminals, in the "
        "spirit of Neue Haas Grotesk Black or Founders Grotesk Bold. The five letters sit on "
        "one baseline, tightly kerned, extruded toward the viewer with visible depth and "
        "chamfered front faces. Shot straight on at a very slight three-quarter angle so the "
        "extrusion reads. The word is the entire subject, centred, filling the frame. "
        "Spelled H-A-R-D-Y, no other text anywhere in the image. " + STEEL
    ),
    "monogram": (
        "A single 3D-printed solid steel letter \"H\" as a monogram mark. Bold, heavy, "
        "geometric, with thick even strokes and squared terminals. Extruded toward the viewer "
        "with visible depth and chamfered edges. Centred, filling the frame, shot straight on "
        "at a very slight three-quarter angle. Only the letter H, no other text. " + STEEL
    ),
    "lockup": (
        "A 3D-printed solid steel brand lockup: a bold geometric capital letter \"H\" mark on "
        "the left, and to its right the word \"HARDY\" in matching bold heavy geometric capitals, "
        "separated by a thin vertical steel rule. All elements extruded toward the viewer with "
        "visible depth and chamfered edges, sitting on one baseline, horizontally centred. "
        "The only text is H and HARDY. " + STEEL
    ),
}


def gen(variant: str, key: str) -> pathlib.Path:
    prompt = VARIANTS[variant]
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={key}",
        data=json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "1:1"}},
        }).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        body = json.loads(r.read())

    for part in body["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            OUT.mkdir(parents=True, exist_ok=True)
            path = OUT / f"{variant}.png"
            path.write_bytes(base64.b64decode(part["inlineData"]["data"]))
            return path
    raise SystemExit(f"{variant}: no image in response — {json.dumps(body)[:400]}")


if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY") or sys.exit("set GEMINI_API_KEY")
    for v in (sys.argv[1:] or ["wordmark"]):
        print(f"{v}: {gen(v, key)}")
