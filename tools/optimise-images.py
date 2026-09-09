#!/usr/bin/env python3
"""Shrink assets/img in place, without changing a single filename, and
without silently degrading anything.

Why in place rather than emitting .webp: every image reference on this
site comes either from build-time markup in render.py or from paths club
volunteers type into the CMS. Switching formats would mean <picture>
elements, a second set of files to keep in step, and a CMS field where
"logo.png" quietly stops working. The savings here come from the two
things that were actually wrong — images stored several times larger than
they are ever displayed, and flat logo art stored as full truecolour —
and neither of those needs a format change.

The important part is the quality gate. Each file is encoded several ways,
most aggressive first, and every candidate is scored against the ORIGINAL
by rendering both at the size the image is actually displayed at, over the
navy the site actually uses (alpha matters: score a logo on white and a
transparent PNG looks catastrophically wrong when it is fine). The first
candidate under MAX_RMS wins; if none pass, the file is left alone. So a
bad result is a no-op rather than a visibly mushy logo nobody notices
until it is live.

Idempotent — see MANIFEST for what makes that true, and for the
generational-loss trap it exists to close. Safe to run after dropping a
new sponsor logo in: unrecognised files get processed, files this tool
already wrote are left alone.

    python3 tools/optimise-images.py            # report only
    python3 tools/optimise-images.py --write    # actually rewrite
"""
import hashlib
import io
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "assets" / "img"

# The ground these images are composited over on the page (--navy-950).
BG = (10, 17, 40)

# Root-mean-square difference, per channel, at display size. Below ~2 is
# imperceptible; 3 is the point where flat colour starts to band visibly.
MAX_RMS = 3.0

# A candidate has to beat the current file by at least this much to be
# worth writing at all.
MIN_SAVING = 0.10

# What actually makes this tool safe to re-run: a record of every file it
# has already produced, by content hash.
#
# The quality gate scores a candidate against "the original" — which, on a
# second run, is whatever is on disk, i.e. the previous run's output. That
# re-baselining is the whole problem. Measured on this repo: a second pass
# wanted to re-encode a logo from JPEG q92 to q88 (a 10% saving, second
# generation loss) and to re-quantise a PNG that had failed the palette
# gate against the full-size original but passed it against the already
# downscaled copy. Both were reported as rms ~2.4 — comfortably "clean" —
# while being exactly the silent degradation the gate exists to prevent.
#
# So: if a file's current bytes are one this tool wrote, leave it alone.
# Anything else — a new sponsor logo, a re-exported photo — is processed
# normally. Delete this file to force a full re-run from source images.
MANIFEST = IMG / ".optimised.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_manifest():
    try:
        return json.loads(MANIFEST.read_text())
    except (OSError, ValueError):
        return {}

# Longest edge to keep. Roughly 3x the largest size each is displayed at,
# measured in the browser — generous enough for a retina phone and a
# future layout change, and still far below what these files were.
BUDGETS = {
    "gallery": 1000,   # carousel, ~700px wide at desktop: recompress only
    "sponsors": 200,   # rendered 64px tall in the wall and the marquee
    "badges": 240,     # rendered ~40px in the hero trust row
}
FIXED = {
    "madmac-badge.jpg": 240,        # rendered 40x40, but small JPEGs artifact fast
    "madmac-wordmark.png": 650,     # the logo — leave room to use it bigger
    "og-madmac-2026.png": 1200,     # fixed by the Open Graph spec
    "apple-touch-icon.png": 180,    # fixed by iOS
    "favicon-32.png": 32,
    "favicon-16.png": 16,
}


# Longest edge each image is actually rendered at, x2 for retina. Measured
# in the browser at both 375px and desktop widths — this is the resolution
# a difference has to be visible at to count as a difference.
SCORE_AT_GROUP = {"gallery": 1000, "sponsors": 160, "badges": 120}
SCORE_AT_FILE = {
    "madmac-badge.jpg": 80,          # rendered 40x40
    "madmac-wordmark.png": 400,      # rendered ~200px wide at most
    "og-madmac-2026.png": 1200,      # shown at full size in a social card
    "apple-touch-icon.png": 180,     # shown at full size on a home screen
    "favicon-32.png": 32,
    "favicon-16.png": 16,
}


def budget_for(path):
    return FIXED.get(path.name) or BUDGETS.get(path.parent.name, 1200)


def score_at(path):
    return SCORE_AT_FILE.get(path.name) or SCORE_AT_GROUP.get(path.parent.name, 1200)


def flatten(im, size):
    """Render over the page background, at display size — the only view of
    an image whose difference from the original actually matters."""
    im = im.convert("RGBA").resize(size, Image.LANCZOS)
    ground = Image.new("RGBA", size, BG + (255,))
    return Image.alpha_composite(ground, im).convert("RGB")


def rms(a, b):
    diff = ImageChops.difference(a, b)
    hist = diff.histogram()
    per_channel = []
    for ch in range(3):
        h = hist[ch * 256:(ch + 1) * 256]
        n = sum(h) or 1
        per_channel.append(math.sqrt(sum(v * (i ** 2) for i, v in enumerate(h)) / n))
    return sum(per_channel) / 3


def candidates(im, suffix):
    """Encodings to try, most aggressive first."""
    if suffix in (".jpg", ".jpeg"):
        # subsampling=0 is 4:4:4 — full chroma resolution. Pillow's default
        # for these qualities is 4:2:0, which halves colour resolution and
        # is fine for photographs and terrible for logo art: it was the
        # single reason every sponsor logo "could not be compressed"
        # (RMS 8.76 on the club badge at 4:2:0 versus 2.59 at 4:4:4, for a
        # file twice the size but still a third of the original).
        for q, sub in ((82, 2), (88, 0), (92, 0), (95, 0)):
            buf = io.BytesIO()
            im.convert("RGB").save(
                buf, "JPEG", quality=q, optimize=True, progressive=True, subsampling=sub
            )
            yield f"jpeg q{q} {'4:4:4' if sub == 0 else '4:2:0'}", buf
        return

    # PNG: try a palette first (flat logo art collapses to almost nothing),
    # then fall back to plain re-encoding, which is lossless.
    if im.mode in ("RGBA", "LA", "P"):
        rgba = im.convert("RGBA")
        for colors in (256, 256):
            buf = io.BytesIO()
            rgba.quantize(colors=colors, method=Image.FASTOCTREE).save(buf, "PNG", optimize=True)
            yield f"png palette {colors}", buf
            break
        buf = io.BytesIO()
        rgba.save(buf, "PNG", optimize=True)
        yield "png rgba lossless", buf
    else:
        rgb = im.convert("RGB")
        buf = io.BytesIO()
        rgb.quantize(colors=256, method=Image.MEDIANCUT).save(buf, "PNG", optimize=True)
        yield "png palette 256", buf
        buf = io.BytesIO()
        rgb.save(buf, "PNG", optimize=True)
        yield "png rgb lossless", buf


def optimise(path, write, manifest):
    before = path.stat().st_size
    rel = str(path.relative_to(ROOT))
    if manifest.get(rel) == sha(path.read_bytes()):
        return before, before, "already optimised (unchanged since last run)"

    im = Image.open(path)
    im.load()

    # A mode "P" image MUST leave palette space before anything resizes it:
    # interpolating palette *indices* blends colour-table positions, not
    # colours, and produces confetti. Several sponsor logos are mode P, and
    # this silently wrecked them before the quality gate caught it.
    if im.mode == "P":
        im = im.convert("RGBA" if "transparency" in im.info else "RGB")

    original = im.copy()
    limit = budget_for(path)
    note = ""
    if max(im.size) > limit:
        # Explicit resize, NOT Image.thumbnail(): thumbnail() calls draft()
        # on JPEGs, which downscales in the DCT domain. It is fast and it is
        # visibly worse — every JPEG here failed the quality gate on that
        # alone, which read as "this image cannot be compressed" when the
        # real problem was how it was being shrunk.
        ow, oh = im.size
        scale = limit / max(ow, oh)
        im = im.resize((max(1, round(ow * scale)), max(1, round(oh * scale))), Image.LANCZOS)
        note = f" {original.size[0]}x{original.size[1]}->{im.size[0]}x{im.size[1]}"

    # Score at the size the image is actually SHOWN at, not the size it is
    # stored at. A sponsor logo is a 64px-tall strip on the page; JPEG
    # ringing in a 200px file that vanishes the moment the browser scales
    # it down to 64 is not a defect worth protecting against, and scoring
    # at storage size rejects perfectly good encodings for it.
    #
    # Aspect ratio is preserved: scoring a 600x242 logo inside a 200x200
    # box squashes reference and candidate by different amounts, and the
    # score becomes meaningless.
    ow, oh = original.size
    scale = min(1.0, score_at(path) / max(ow, oh))
    display = (max(1, round(ow * scale)), max(1, round(oh * scale)))
    reference = flatten(original, display)

    for label, buf in candidates(im, path.suffix.lower()):
        size = len(buf.getvalue())
        if size > before * (1 - MIN_SAVING):
            continue
        buf.seek(0)
        score = rms(reference, flatten(Image.open(buf), display))
        if score <= MAX_RMS:
            if write:
                data = buf.getvalue()
                path.write_bytes(data)
                manifest[rel] = sha(data)
            return before, size, f"{label}{note} (rms {score:.2f})"

    return before, before, "left alone — nothing beat the quality gate"


def main():
    write = "--write" in sys.argv
    files = sorted(
        p for p in IMG.rglob("*")
        if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png")
    )
    manifest = load_manifest()
    total_before = total_after = 0
    rows = []
    for path in files:
        before, after, note = optimise(path, write, manifest)
        total_before += before
        total_after += after
        rows.append((path.relative_to(ROOT), before, after, note))

    rows.sort(key=lambda r: r[1] - r[2], reverse=True)
    for rel, before, after, note in rows:
        if after == before:
            print(f"{before/1024:8.1f}KB {'':>14}  {rel}  {note}")
        else:
            print(f"{before/1024:8.1f}KB -> {after/1024:7.1f}KB  ({100*(1-after/before):4.1f}% off)  {rel}  {note}")

    print()
    print(f"total {total_before/1024:.1f}KB -> {total_after/1024:.1f}KB "
          f"({100*(1-total_after/total_before):.1f}% smaller)")
    if write:
        MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    if not write:
        print("\ndry run — nothing written. Re-run with --write to apply.")


if __name__ == "__main__":
    main()
