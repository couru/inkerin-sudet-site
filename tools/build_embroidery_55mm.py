from __future__ import annotations

from collections import deque
from pathlib import Path
import subprocess
import zipfile

import numpy as np
from PIL import Image, ImageDraw

from build_embroidery_variants import (
    INKSCAPE,
    PRODUCTION,
    boundary_loops,
    simplify,
)


SIZE_MM = 55
CANVAS = 700
PX_PER_MM = CANVAS / SIZE_MM
MIN_LINE_PX = PX_PER_MM  # 12.727 px = 1 mm
NAME = "inkerin-sudet-55mm"
FOLDER = PRODUCTION / "55mm"
PACKAGE = PRODUCTION / f"{NAME}-production-package.zip"
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools" / "source" / "inkerin-sudet-55mm-generated-master.png"

# Approved brighter graphite palette; black is supplied by cap fabric.
PALETTE = np.array([
    (5, 6, 6),
    (172, 172, 173),
    (115, 114, 118),
    (71, 72, 75),
    (134, 113, 77),
    (17, 51, 85),
    (102, 39, 37),
], dtype=np.uint8)


def remove_small_components(mask: np.ndarray, minimum_area: int) -> np.ndarray:
    height, width = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    result = np.zeros_like(mask, dtype=bool)
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]:
            continue
        queue = deque([(y, x)])
        seen[y, x] = True
        component = []
        while queue:
            cy, cx = queue.popleft()
            component.append((cy, cx))
            for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    queue.append((ny, nx))
        if len(component) >= minimum_area:
            ys, xs = zip(*component)
            result[np.asarray(ys), np.asarray(xs)] = True
    return result


def embroidery_safe_masks(labels: np.ndarray) -> dict[int, np.ndarray]:
    masks = {}
    for index in range(1, 7):
        mask = labels == index
        masks[index] = remove_small_components(mask, int(MIN_LINE_PX * MIN_LINE_PX))
    return masks


def labels_from_generated() -> np.ndarray:
    image = Image.open(SOURCE).convert("RGBA")
    image = image.resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    rgba = np.asarray(image)
    rgb = rgba[:, :, :3].astype(np.int32)
    palette = PALETTE.astype(np.int32)
    distance = ((rgb[:, :, None, :] - palette[None, None, :, :]) ** 2).sum(axis=3)
    labels = distance.argmin(axis=2).astype(np.uint8)
    labels[rgba[:, :, 3] < 128] = 255
    return labels


def render_png(masks: dict[int, np.ndarray]) -> Image.Image:
    output = np.zeros((CANVAS, CANVAS, 4), dtype=np.uint8)
    for index in (4, 5, 6, 2, 3, 1):
        mask = masks[index]
        output[mask, :3] = PALETTE[index]
        output[mask, 3] = 255
    return Image.fromarray(output, "RGBA")


def render_svg(masks: dict[int, np.ndarray]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE_MM}mm" height="{SIZE_MM}mm" viewBox="0 0 {CANVAS} {CANVAS}">',
        '<title>Inkerin Sudet — embroidery artwork, 55 mm</title>',
        '<desc>Minimum visible feature 1 mm. Black areas are cap-fabric/no-sew separators. Vector paths only.</desc>',
    ]
    for index in (4, 5, 6, 2, 3, 1):
        paths = []
        for loop in boundary_loops(masks[index]):
            if len(loop) < MIN_LINE_PX * 4:
                continue
            points = simplify(loop + [loop[0]], epsilon=0.8)
            paths.append("M " + " L ".join(f"{x} {y}" for x, y in points) + " Z")
        if paths:
            color = "#%02X%02X%02X" % tuple(PALETTE[index])
            lines.append(
                f'<path fill="{color}" fill-rule="evenodd" d="{" ".join(paths)}"/>'
            )
    lines.append("</svg>")
    return "\n".join(lines)


def make_preview(image: Image.Image, path: Path) -> None:
    canvas = Image.new("RGB", (1400, 1400), (5, 6, 6))
    draw = ImageDraw.Draw(canvas)
    for y in range(1400):
        shade = 5 + (y // 8) % 5
        draw.line((0, y, 1400, y), fill=(shade, shade + 1, shade + 1))
    emblem = image.copy()
    emblem.thumbnail((1100, 1100), Image.Resampling.LANCZOS)
    canvas.paste(emblem, (150, 150), emblem)
    canvas.save(path, optimize=True)


def readme() -> str:
    colors = ", ".join("#%02X%02X%02X" % tuple(PALETTE[i]) for i in range(1, 7))
    return f'''# Inkerin Sudet — производственный макет 55 мм

Макет оптимизирован для фронтальной вышивки на чёрной кепке.

## Параметры

- итоговое поле: **55 × 55 мм**;
- минимальная толщина производственных контуров: **1 мм**;
- изолированные элементы меньше 1 × 1 мм удалены;
- технологические разделительные контуры заданы толщиной 1 мм;
- чёрные области обозначают ткань кепки и технологические зоны без зашивки;
- цвета нитей: {colors};
- SVG и EPS содержат только кривые, без шрифтов и встроенного растра.

## Файлы

- `{NAME}.eps` — основной производственный векторный макет;
- `{NAME}.svg` — редактируемая векторная копия;
- `{NAME}.png` — прозрачный эталон цветоделения;
- `{NAME}-black-cap-preview.png` — превью на чёрной ткани.

Перед запуском требуется оцифровка в DST/PES под конкретную машину, назначение направлений и плотности стежков, компенсация стягивания и пробный отшив.
'''


def main() -> None:
    FOLDER.mkdir(parents=True, exist_ok=True)
    labels = labels_from_generated()
    masks = embroidery_safe_masks(labels)
    png = FOLDER / f"{NAME}.png"
    svg = FOLDER / f"{NAME}.svg"
    eps = FOLDER / f"{NAME}.eps"
    preview = FOLDER / f"{NAME}-black-cap-preview.png"
    notes = FOLDER / "README.md"
    svg.write_text(render_svg(masks), encoding="utf-8")
    subprocess.run([str(INKSCAPE), str(svg), "--export-filename", str(eps)], check=True)
    subprocess.run([
        str(INKSCAPE), str(svg), "--export-filename", str(png),
        "--export-width", "1400", "--export-height", "1400",
        "--export-background-opacity", "0",
    ], check=True)
    image = Image.open(png).convert("RGBA")
    make_preview(image, preview)
    notes.write_text(readme(), encoding="utf-8")
    with zipfile.ZipFile(PACKAGE, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in (png, svg, eps, preview, notes):
            archive.write(path, path.name)
    print(PACKAGE)


if __name__ == "__main__":
    main()
