"""Rebuild the gray-cap production vector from the approved flat artwork."""
from __future__ import annotations

import ctypes as C
import os
from pathlib import Path
import subprocess
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
INK = Path(r"C:\Program Files\Inkscape\bin")
NAME = "inkerin-sudet-gray-cap-55mm"
PRODUCTION = ROOT / "public/assets/production"
OUT = PRODUCTION / "gray-cap-55mm"
SOURCE = ROOT / "tools/source/inkerin-sudet-gray-cap-reference.png"
HEIGHT_MM = 55


class Point(C.Structure):
    _fields_ = [("x", C.c_double), ("y", C.c_double)]


class Curve(C.Structure):
    _fields_ = [("n", C.c_int), ("tag", C.POINTER(C.c_int)), ("c", C.POINTER(Point * 3))]


class TracePath(C.Structure):
    pass


TracePath._fields_ = [
    ("area", C.c_int), ("sign", C.c_int), ("curve", Curve), ("next", C.POINTER(TracePath)),
]


class State(C.Structure):
    _fields_ = [("status", C.c_int), ("paths", C.POINTER(TracePath))]


class Bitmap(C.Structure):
    _fields_ = [("w", C.c_int), ("h", C.c_int), ("dy", C.c_int), ("map", C.POINTER(C.c_ulong))]


def trace(mask: np.ndarray, lib) -> str:
    height, width = mask.shape
    words = (width + 31) // 32
    packed = np.packbits(np.pad(mask, ((0, 0), (0, words * 32 - width))), axis=1)
    data = np.ascontiguousarray(packed.view(">u4"), dtype=np.uint32)
    bitmap = Bitmap(width, height, words, data.ctypes.data_as(C.POINTER(C.c_ulong)))
    param = lib.potrace_param_default()
    state = lib.potrace_trace(param, C.byref(bitmap))
    try:
        if not state or state.contents.status:
            raise RuntimeError("Potrace could not trace the mask")
        path = state.contents.paths
        result = []
        while path:
            curve = path.contents.curve

            def point(p: Point) -> str:
                return f"{p.x:.3f} {p.y:.3f}"

            result.append("M" + point(curve.c[curve.n - 1][2]))
            for i in range(curve.n):
                a, b, c = curve.c[i]
                if curve.tag[i] == 1:
                    result.append(f"C{point(a)} {point(b)} {point(c)}")
                else:
                    result.append(f"L{point(b)} {point(c)}")
            result.append("Z")
            path = path.contents.next
        return " ".join(result)
    finally:
        if state:
            lib.potrace_state_free(state)
        lib.potrace_param_free(param)


def disk(mask: np.ndarray, radius: int, dilate: bool) -> np.ndarray:
    """Binary disk morphology, with a false border."""
    h, w = mask.shape
    padded = np.pad(mask, radius)
    result = np.full_like(mask, not dilate)
    combine = np.logical_or if dilate else np.logical_and
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                y, x = radius + dy, radius + dx
                combine(result, padded[y:y + h, x:x + w], out=result)
    return result


def opening(mask: np.ndarray, radius: int) -> np.ndarray:
    return disk(disk(mask, radius, False), radius, True)


def header_letters(bright: np.ndarray) -> np.ndarray:
    """Separate the seven solid glyphs from the connected banner."""
    x0, y0, x1, y1 = 153, 54, 478, 120
    roi = bright[y0:y1, x0:x1]
    regions = Image.fromarray(roi.astype(np.uint8), "L")
    for x in range(roi.shape[1]):
        ImageDraw.floodfill(regions, (x, 0), 2)
        ImageDraw.floodfill(regions, (x, roi.shape[0] - 1), 2)
    for y in range(roi.shape[0]):
        ImageDraw.floodfill(regions, (0, y), 2)
        ImageDraw.floodfill(regions, (roi.shape[1] - 1, y), 2)
    letters = np.zeros_like(bright)
    letters[y0:y1, x0:x1] = np.asarray(regions) == 1
    return opening(letters, 2)


def source_layers():
    original = Image.open(SOURCE).convert("RGBA")
    image = original.resize((627, 627), Image.Resampling.LANCZOS)
    rgba = np.asarray(image)
    gray = np.asarray(image.convert("L").filter(ImageFilter.GaussianBlur(.65)))
    silhouette = opening(rgba[..., 3] >= 128, 2)
    ys, xs = np.nonzero(silhouette)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    width, height = int(x1 - x0), int(y1 - y0)
    # Six tracing pixels are about 0.53 mm. Remove narrow stray islands
    # while keeping normal corners and widening the recognizable light strokes.
    radius = int(np.ceil(height / HEIGHT_MM / 2))
    bright = gray >= 140
    letters = header_letters(bright)
    widened = disk(bright & ~disk(letters, 2, True), 2, True)
    medium = opening((gray >= 94) & silhouette & ~disk(letters, 2, True), radius)
    light = opening(widened & silhouette, radius)
    # The banner rails are continuous: preserve their smooth long edges.
    light[:142] = opening(widened & silhouette, 3)[:142]
    light |= disk(letters, 1, True)
    # Simplify the eyelights to rounded bands; retain the separation from the brow.
    yy, xx = np.ogrid[:gray.shape[0], :gray.shape[1]]
    eyes = np.s_[343:369, 263:362]
    light[eyes] = opening(bright & silhouette, 2)[eyes]
    for cx in (280.5, 346.5):
        pupil = (xx - cx) ** 2 + (yy - 349.5) ** 2 <= 6.4 ** 2
        light[pupil] = False
        medium[pupil] = False
    dark = opening((gray >= 43) & silhouette, radius)
    # Avoid a thin extra shade tracing the entire crest and landscape.
    dark[:221] = False
    dark[487:] = False
    dark[:, :197] = False
    dark[:, 430:] = False
    # Keep the tape bars separated by black rather than by gray artifacts.
    for x in (83, 105, 127):
        light[492:530, x:x + 12] = False
        medium[492:530, x:x + 12] = False
    grip = np.s_[493:530, 63:140]
    medium[grip] = False
    # Rebuild the small grip blocks as contiguous silver areas.
    light[495:527, 89:127] |= ((xx >= 95) & (xx < 105) | (xx >= 117) & (xx < 127))[:, 89:127]
    layers = [
        ("shield-black", "#171719", silhouette),
        ("dark-graphite", "#47484B", dark),
        ("mid-graphite", "#737276", medium | light),
        ("silver-graphite", "#ACACAD", light),
    ]
    return width, height, [(name, color, mask[y0:y1, x0:x1]) for name, color, mask in layers]


def main() -> None:
    with os.add_dll_directory(str(INK)):
        lib = C.CDLL(str(INK / "libpotrace-0.dll"))
        lib.potrace_param_default.restype = C.c_void_p
        lib.potrace_trace.argtypes = [C.c_void_p, C.POINTER(Bitmap)]
        lib.potrace_trace.restype = C.POINTER(State)
        lib.potrace_state_free.argtypes = [C.POINTER(State)]
        lib.potrace_param_free.argtypes = [C.c_void_p]
        width, height, layers = source_layers()
        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width * HEIGHT_MM / height:.5f}mm" '
            f'height="{HEIGHT_MM}mm" viewBox="0 0 {width} {height}">',
            "<title>INKERIN SUDET — 55 mm for gray cap</title>",
            "<desc>Four-color vector traced from the supplied flat artwork. Nearly black areas use black thread.</desc>",
        ]
        for name, color, mask in layers:
            svg.append(f'  <path id="{name}" fill="{color}" fill-rule="evenodd" d="{trace(mask, lib)}"/>')
        svg.append("</svg>")
    paths = {ext: OUT / f"{NAME}.{ext}" for ext in ("svg", "eps", "png")}
    paths["svg"].write_text("\n".join(svg) + "\n", encoding="utf-8")
    for ext, args in [("eps", ["--export-area-page"]), ("png", ["--export-dpi=600"])]:
        subprocess.run(
            [str(INK / "inkscape.com"), str(paths["svg"]), f"--export-filename={paths[ext]}", *args],
            check=True,
        )
    eps = paths["eps"]
    eps.write_bytes(b"\n".join(line.rstrip() for line in eps.read_bytes().split(b"\n")))
    with zipfile.ZipFile(PRODUCTION / f"{NAME}.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in (*paths.values(), OUT / "production-notes.txt", OUT / "gray-cap-black-visor-preview.png"):
            archive.write(path, path.name)


if __name__ == "__main__":
    main()
