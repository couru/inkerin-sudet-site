from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
import math
import shutil
import subprocess
import zipfile

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "assets" / "production"
SOURCE_PNG = ROOT / "tools" / "source" / "inkerin-sudet-cap-emblem-color-master.png"
PNG = OUT / "inkerin-sudet-cap-emblem-embroidery.png"
SVG = OUT / "inkerin-sudet-cap-emblem-embroidery.svg"
EPS = OUT / "inkerin-sudet-cap-emblem-embroidery.eps"
PREVIEW = OUT / "inkerin-sudet-cap-emblem-black-cap-preview.png"
ZIP = OUT / "inkerin-sudet-cap-emblem-production-package.zip"
README = OUT / "README.md"

SOURCE_PALETTE = np.array(
    [
        (8, 12, 17),       # near-black
        (255, 255, 255),   # white
        (205, 209, 213),   # light gray
        (135, 139, 143),   # medium gray
        (255, 190, 0),     # gold
        (5, 78, 174),      # royal blue
        (225, 25, 42),     # muted red
    ],
    dtype=np.int16,
)

# Palette sampled from the approved dark Karjalan Karhut embroidery reference.
# Black is supplied by the cap fabric, not by thread.
THREAD_PALETTE = np.array(
    [
        (5, 6, 6),         # transparent / black cap fabric
        (81, 84, 87),      # light graphite
        (58, 61, 64),      # medium graphite
        (34, 36, 38),      # dark graphite
        (116, 104, 78),    # graphite gold
        (43, 77, 98),      # muted dark blue
        (123, 48, 47),     # muted dark red
    ],
    dtype=np.uint8,
)


def remove_checkerboard(image: Image.Image) -> Image.Image:
    rgb = np.asarray(image.convert("RGB"))
    h, w, _ = rgb.shape
    spread = rgb.max(axis=2) - rgb.min(axis=2)
    allowed = (spread <= 14) & (rgb.mean(axis=2) >= 170)
    outside = np.zeros((h, w), dtype=bool)
    queue: deque[tuple[int, int]] = deque()
    for x in range(w):
        if allowed[0, x]: queue.append((0, x))
        if allowed[h - 1, x]: queue.append((h - 1, x))
    for y in range(h):
        if allowed[y, 0]: queue.append((y, 0))
        if allowed[y, w - 1]: queue.append((y, w - 1))
    while queue:
        y, x = queue.popleft()
        if outside[y, x] or not allowed[y, x]:
            continue
        outside[y, x] = True
        if y: queue.append((y - 1, x))
        if y + 1 < h: queue.append((y + 1, x))
        if x: queue.append((y, x - 1))
        if x + 1 < w: queue.append((y, x + 1))
    rgba = np.dstack((rgb, np.where(outside, 0, 255).astype(np.uint8)))
    return Image.fromarray(rgba, "RGBA")


def quantize(image: Image.Image, size: int = 700) -> tuple[Image.Image, np.ndarray]:
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    rgba = np.asarray(image)
    rgb = rgba[:, :, :3].astype(np.int32)
    dist = ((rgb[:, :, None, :] - SOURCE_PALETTE[None, None, :, :]) ** 2).sum(axis=3)
    labels = dist.argmin(axis=2).astype(np.uint8)
    alpha = rgba[:, :, 3]
    labels[alpha < 128] = 255
    out = np.zeros((*labels.shape, 4), dtype=np.uint8)
    visible = labels != 255
    # Near-black artwork is left transparent so the black cap supplies it.
    visible &= labels != 0
    out[visible, :3] = THREAD_PALETTE[labels[visible]]
    out[visible, 3] = 255
    return Image.fromarray(out, "RGBA"), labels


def boundary_loops(mask: np.ndarray) -> list[list[tuple[int, int]]]:
    h, w = mask.shape
    edges: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if y == 0 or not mask[y - 1, x]: edges[(x, y)].append((x + 1, y))
        if x == w - 1 or not mask[y, x + 1]: edges[(x + 1, y)].append((x + 1, y + 1))
        if y == h - 1 or not mask[y + 1, x]: edges[(x + 1, y + 1)].append((x, y + 1))
        if x == 0 or not mask[y, x - 1]: edges[(x, y + 1)].append((x, y))
    loops: list[list[tuple[int, int]]] = []
    while edges:
        start = next(iter(edges))
        loop = [start]
        current = start
        while True:
            options = edges.get(current)
            if not options:
                break
            nxt = options.pop()
            if not options:
                del edges[current]
            if nxt == start:
                break
            loop.append(nxt)
            current = nxt
        if len(loop) >= 8:
            loops.append(loop)
    return loops


def point_line_distance(p, a, b) -> float:
    if a == b:
        return math.dist(p, a)
    x, y = p; x1, y1 = a; x2, y2 = b
    return abs((y2-y1)*x - (x2-x1)*y + x2*y1 - y2*x1) / math.hypot(y2-y1, x2-x1)


def simplify(points: list[tuple[int, int]], epsilon: float = 1.1) -> list[tuple[int, int]]:
    if len(points) < 3:
        return points
    first, last = points[0], points[-1]
    distances = [point_line_distance(p, first, last) for p in points[1:-1]]
    if not distances or max(distances) <= epsilon:
        return [first, last]
    index = distances.index(max(distances)) + 1
    return simplify(points[: index + 1], epsilon)[:-1] + simplify(points[index:], epsilon)


def make_svg(labels: np.ndarray) -> str:
    h, w = labels.shape
    chunks = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="100mm" viewBox="0 0 {w} {h}">',
        '<title>Inkerin Sudet cap embroidery artwork</title>',
        '<desc>Seven flat thread colors; transparent areas represent black cap fabric. All artwork is vector paths.</desc>',
    ]
    # Paint broad colors first and detail colors last.
    for idx in (4, 5, 6, 2, 3, 1):
        loops = boundary_loops(labels == idx)
        parts = []
        for loop in loops:
            if len(loop) < 12:
                continue
            pts = simplify(loop + [loop[0]], 1.1)
            parts.append("M " + " L ".join(f"{x} {y}" for x, y in pts) + " Z")
        if parts:
            color = "#%02X%02X%02X" % tuple(THREAD_PALETTE[idx])
            chunks.append(f'<path fill="{color}" fill-rule="evenodd" d="{" ".join(parts)}"/>')
    chunks.append("</svg>")
    return "\n".join(chunks)


def make_preview(image: Image.Image) -> None:
    canvas = Image.new("RGB", (1400, 1400), (24, 25, 28))
    draw = ImageDraw.Draw(canvas)
    for y in range(1400):
        shade = int(24 + 9 * math.sin(y / 34.0))
        draw.line((0, y, 1400, y), fill=(shade, shade, shade + 2))
    emblem = image.copy()
    emblem.thumbnail((1080, 1080), Image.Resampling.LANCZOS)
    x = (1400 - emblem.width) // 2
    y = (1400 - emblem.height) // 2
    canvas.paste(emblem, (x, y), emblem)
    canvas.save(PREVIEW, optimize=True)


def main() -> None:
    cleaned = remove_checkerboard(Image.open(SOURCE_PNG))
    artwork, labels = quantize(cleaned)
    artwork.save(PNG, optimize=True)
    SVG.write_text(make_svg(labels), encoding="utf-8")
    make_preview(artwork)
    inkscape = Path(r"C:\Program Files\Inkscape\bin\inkscape.exe")
    subprocess.run([str(inkscape), str(SVG), "--export-filename", str(EPS)], check=True)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in (PNG, SVG, EPS, PREVIEW, README):
            archive.write(path, path.name)
    print(f"Built {ZIP}")


if __name__ == "__main__":
    main()




