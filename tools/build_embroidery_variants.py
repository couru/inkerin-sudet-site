from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import math
import subprocess
import zipfile

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools" / "source" / "inkerin-sudet-cap-emblem-color-master.png"
PRODUCTION = ROOT / "public" / "assets" / "production"
INKSCAPE = Path(r"C:\Program Files\Inkscape\bin\inkscape.exe")

SOURCE_PALETTE = np.array([
    (8, 12, 17), (255, 255, 255), (205, 209, 213), (135, 139, 143),
    (255, 190, 0), (5, 78, 174), (225, 25, 42),
], dtype=np.int32)

VARIANTS = {
    "graphite": {
        "title": "графитовый",
        "palette": [(5, 6, 6), (172, 172, 173), (115, 114, 118), (71, 72, 75),
                    (134, 113, 77), (17, 51, 85), (102, 39, 37)],
    },
    "graphite-dark": {
        "title": "тёмный графитовый",
        "palette": [(5, 6, 6), (95, 95, 97), (66, 66, 68), (35, 36, 38),
                    (83, 71, 55), (16, 35, 52), (69, 30, 29)],
    },
}


def labels_from_source(size: int = 700) -> np.ndarray:
    image = Image.open(SOURCE).convert("RGBA")
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    rgba = np.asarray(image)
    rgb = rgba[:, :, :3].astype(np.int32)
    dist = ((rgb[:, :, None, :] - SOURCE_PALETTE[None, None, :, :]) ** 2).sum(axis=3)
    labels = dist.argmin(axis=2).astype(np.uint8)
    labels[rgba[:, :, 3] < 128] = 255
    return labels


def boundary_loops(mask: np.ndarray) -> list[list[tuple[int, int]]]:
    h, w = mask.shape
    edges: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if y == 0 or not mask[y - 1, x]: edges[(x, y)].append((x + 1, y))
        if x == w - 1 or not mask[y, x + 1]: edges[(x + 1, y)].append((x + 1, y + 1))
        if y == h - 1 or not mask[y + 1, x]: edges[(x + 1, y + 1)].append((x, y + 1))
        if x == 0 or not mask[y, x - 1]: edges[(x, y + 1)].append((x, y))
    loops = []
    while edges:
        start = next(iter(edges)); current = start; loop = [start]
        while True:
            options = edges.get(current)
            if not options: break
            nxt = options.pop()
            if not options: del edges[current]
            if nxt == start: break
            loop.append(nxt); current = nxt
        if len(loop) >= 8: loops.append(loop)
    return loops


def distance(p, a, b) -> float:
    if a == b: return math.dist(p, a)
    x, y = p; x1, y1 = a; x2, y2 = b
    return abs((y2-y1)*x-(x2-x1)*y+x2*y1-y2*x1) / math.hypot(y2-y1, x2-x1)


def simplify(points, epsilon=1.1):
    if len(points) < 3: return points
    ds = [distance(p, points[0], points[-1]) for p in points[1:-1]]
    if not ds or max(ds) <= epsilon: return [points[0], points[-1]]
    i = ds.index(max(ds)) + 1
    return simplify(points[:i+1], epsilon)[:-1] + simplify(points[i:], epsilon)


def render_png(labels: np.ndarray, palette: np.ndarray) -> Image.Image:
    out = np.zeros((*labels.shape, 4), dtype=np.uint8)
    for idx in range(1, 7):
        mask = labels == idx
        out[mask, :3] = palette[idx]
        out[mask, 3] = 255
    return Image.fromarray(out, "RGBA")


def render_svg(labels: np.ndarray, palette: np.ndarray, title: str) -> str:
    h, w = labels.shape
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             f'<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="100mm" viewBox="0 0 {w} {h}">',
             f'<title>Inkerin Sudet — {title} cap embroidery artwork</title>',
             '<desc>Six thread colors. Transparent areas use black cap fabric. Vector paths only.</desc>']
    for idx in (4, 5, 6, 2, 3, 1):
        paths = []
        for loop in boundary_loops(labels == idx):
            if len(loop) < 12: continue
            points = simplify(loop + [loop[0]])
            paths.append('M ' + ' L '.join(f'{x} {y}' for x, y in points) + ' Z')
        if paths:
            color = '#%02X%02X%02X' % tuple(palette[idx])
            lines.append(f'<path fill="{color}" fill-rule="evenodd" d="{" ".join(paths)}"/>')
    lines.append('</svg>')
    return '\n'.join(lines)


def preview(image: Image.Image, path: Path) -> None:
    canvas = Image.new("RGB", (1400, 1400), (5, 6, 6))
    draw = ImageDraw.Draw(canvas)
    for y in range(1400):
        shade = 5 + int(5 * (1 + math.sin(y / 28)))
        draw.line((0, y, 1400, y), fill=(shade, shade + 1, shade + 1))
    emblem = image.copy(); emblem.thumbnail((1080, 1080), Image.Resampling.LANCZOS)
    canvas.paste(emblem, ((1400-emblem.width)//2, (1400-emblem.height)//2), emblem)
    canvas.save(path, optimize=True)


def readme(name: str, title: str, palette: np.ndarray) -> str:
    colors = ', '.join('#%02X%02X%02X' % tuple(palette[i]) for i in range(1, 7))
    return f'''# Inkerin Sudet — {title} макет вышивки

Комплект для фронтальной вышивки на чёрной бейсболке.

## Содержимое

- `inkerin-sudet-{name}.eps` — основной производственный векторный макет;
- `inkerin-sudet-{name}.svg` — редактируемая векторная копия;
- `inkerin-sudet-{name}.png` — прозрачный эталон цветоделения;
- `inkerin-sudet-{name}-black-cap-preview.png` — превью на чёрной ткани.

## Параметры

- рабочее поле: 100 × 100 мм; минимальная рекомендуемая высота — 85 мм;
- цвета нитей: {colors};
- чёрный цвет обеспечивает ткань кепки и не зашивается;
- SVG и EPS содержат только кривые, без шрифтов и встроенного растра;
- перед производством требуется оцифровка в DST/PES под конкретную машину и пробный отшив.
'''


def build(name: str, spec: dict, labels: np.ndarray) -> None:
    folder = PRODUCTION / name; folder.mkdir(parents=True, exist_ok=True)
    palette = np.asarray(spec["palette"], dtype=np.uint8)
    base = f"inkerin-sudet-{name}"
    png = folder / f"{base}.png"; svg = folder / f"{base}.svg"
    eps = folder / f"{base}.eps"; prev = folder / f"{base}-black-cap-preview.png"
    notes = folder / "README.md"; package = PRODUCTION / f"{base}-production-package.zip"
    image = render_png(labels, palette); image.save(png, optimize=True)
    svg.write_text(render_svg(labels, palette, spec["title"]), encoding="utf-8")
    subprocess.run([str(INKSCAPE), str(svg), "--export-filename", str(eps)], check=True)
    preview(image, prev); notes.write_text(readme(name, spec["title"], palette), encoding="utf-8")
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in (png, svg, eps, prev, notes): archive.write(path, path.name)
    print(package)


def main() -> None:
    labels = labels_from_source()
    for name, spec in VARIANTS.items(): build(name, spec, labels)


if __name__ == "__main__":
    main()



