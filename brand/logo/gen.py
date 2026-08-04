#!/usr/bin/env python3
import base64
import json
import os
import pathlib
import sys
import urllib.request

MODEL = "gemini-3-pro-image"
ASPECT = {"wordmark": "16:9", "monogram": "1:1"}
OUT = pathlib.Path(__file__).parent / "_work"

STEEL = (
    "Material: solid machined stainless steel with a brushed satin finish, covered in fine "
    "rigid scratches and micro-abrasions from real use. Reflective but not chrome — it catches "
    "light in soft broad highlights, not mirror glare. Each bevelled edge carries a thin, "
    "restrained warm brass edge — a crisp bright line exactly one bevel wide, like polished "
    "brass catching light. "
    "Lit evenly by a large soft studio softbox from the upper left, with gentle fill from the "
    "right so the front faces stay bright and legible. Calm, even, catalogue lighting. "
    "Background: pure solid black, #000000, completely flat and featureless. "
    "ABSOLUTELY NO glow, NO bloom, NO halo, NO light spill onto the background, NO neon, "
    "NO gaming or movie-poster aesthetic, NO orange atmosphere, NO vignette, NO reflections "
    "on the floor. The background stays pure unlit black everywhere. "
    "Clean industrial product photography of a machined metal object, sharp focus, high detail."
)

VARIANTS = {
    "wordmark": (
        "A machined solid steel wordmark reading exactly \"HARDY\" in capital letters. "
        "The letterforms are WIDE and EXTENDED — each letter is noticeably wider than it is "
        "tall, with thick even strokes, large open counters and squared terminals, in the "
        "spirit of Helvetica Black Extended or Archivo Expanded. Heavy, bulky, industrial, "
        "and unmistakably WIDE, never condensed or tall. The five letters sit on one baseline "
        "in a single horizontal row, evenly kerned, extruded toward the viewer with shallow "
        "visible depth and chamfered front faces. Shot straight on, front-facing, with only a "
        "very slight downward angle so the extrusion reads. The word fills the frame "
        "horizontally as one wide horizontal block. "
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
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": ASPECT.get(variant, "1:1")}},
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
