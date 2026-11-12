"""Rebuild the gray-cap production vector from the approved flat artwork."""
from __future__ import annotations

import ctypes as C
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

import numpy as np
from PIL import Image


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


class TraceParams(C.Structure):
    # Public prefix of potrace_param_t. Lower alphamax keeps sharp corners.
    _fields_ = [
        ("turdsize", C.c_int), ("turnpolicy", C.c_int), ("alphamax", C.c_double),
        ("opticurve", C.c_int), ("opttolerance", C.c_double),
    ]


def trace(mask: np.ndarray, lib) -> str:
    height, width = mask.shape
    words = (width + 31) // 32
    packed = np.packbits(np.pad(mask, ((0, 0), (0, words * 32 - width))), axis=1)
    data = np.ascontiguousarray(packed.view(">u4"), dtype=np.uint32)
    bitmap = Bitmap(width, height, words, data.ctypes.data_as(C.POINTER(C.c_ulong)))
    param = lib.potrace_param_default()
    if not param:
        raise RuntimeError("Could not allocate Potrace parameters")
    settings = C.cast(param, C.POINTER(TraceParams)).contents
    settings.turdsize = 12
    settings.alphamax = .65
    settings.opttolerance = .12
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


def source_layers():
    image = Image.open(SOURCE).convert("RGBA")
    rgba = np.asarray(image)
    gray = np.asarray(image.convert("L"))
    silhouette = rgba[..., 3] >= 128
    ys, xs = np.nonzero(silhouette)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    width, height = int(x1 - x0), int(y1 - y0)
    # Trace the tonal boundaries at source resolution, with no geometry edits.
    layers = [
        ("shield-black", "#070707", silhouette),
        ("dark-graphite", "#4B4B4D", silhouette & (gray >= 43)),
        ("mid-graphite", "#737175", silhouette & (gray >= 94)),
        ("silver-graphite", "#ADADAF", silhouette & (gray >= 140)),
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
    shutil.copyfile(SOURCE, paths["png"])
    subprocess.run(
        [str(INK / "inkscape.com"), str(paths["svg"]), f"--export-filename={paths['eps']}", "--export-area-page"],
        check=True,
    )
    eps = paths["eps"]
    eps.write_bytes(b"\n".join(line.rstrip() for line in eps.read_bytes().split(b"\n")))
    with zipfile.ZipFile(PRODUCTION / f"{NAME}.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in (*paths.values(), OUT / "production-notes.txt", OUT / "gray-cap-black-visor-preview.png"):
            archive.write(path, path.name)


if __name__ == "__main__":
    main()
