#!/usr/bin/env python3
"""
gif_to_header.py

Convert a GIF into a C header that matches the layout used by
`src/dancing.hpp` in this repo: it emits an `#include <Animation.hpp>`,
a `const uint16_t <name>[frames][width*height]` array with per-pixel
entries in the form `color565(R, G, B)` arranged by rows (annotated
with `/*row*/` comments), and a `double <name>_frame_time` with the
seconds-per-frame value.

Usage:
    python tools\gif_to_header.py input.gif -o src\output.hpp -n animation_name

Notes:
- Requires Pillow (`pip install Pillow`).
- Assumes default size 64x64 unless overridden with --width/--height.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple, Optional

from PIL import Image, ImageSequence


def sanitize_varname(name: str) -> str:
    out = []
    for c in name:
        if c.isalnum() or c == '_':
            out.append(c)
        else:
            out.append('_')
    s = ''.join(out)
    if not s:
        s = 'gif_image'
    if s[0].isdigit():
        s = 'img_' + s
    return s


def frame_durations_ms(img: Image.Image) -> List[int]:
    durations: List[int] = []
    for frame in ImageSequence.Iterator(img):
        dur = frame.info.get('duration', 100)
        durations.append(int(dur))
    return durations


def rgba_to_rgb(bg: Tuple[int, int, int], px: Tuple[int, int, int, int]) -> Tuple[int, int, int]:
    r, g, b, a = px
    if a >= 255:
        return (r, g, b)
    alpha = a / 255.0
    return (
        int(r * alpha + bg[0] * (1 - alpha)),
        int(g * alpha + bg[1] * (1 - alpha)),
        int(b * alpha + bg[2] * (1 - alpha)),
    )


def extract_frames(path: Path, size: Tuple[int, int]) -> Tuple[List[Image.Image], float]:
    with Image.open(path) as img:
        durations = frame_durations_ms(img)
        if durations:
            ms = sum(durations) / len(durations)
        else:
            ms = img.info.get('duration', 100)

        frames: List[Image.Image] = []
        for frame in ImageSequence.Iterator(img):
            fr = frame.convert('RGBA')
            if fr.size != size:
                fr = fr.resize(size, Image.NEAREST)
            frames.append(fr)

    return frames, (ms / 1000.0)


def write_c_header(path: Path, varname: str, frames: List[Image.Image], frame_time_s: float, width: int, height: int, bg: Tuple[int, int, int] = (0, 0, 0)) -> None:
    lines: List[str] = []
    lines.append('#include <Animation.hpp>\n')
    lines.append(f'// Each frame is an array of {width*height} uint16_t pixels (width*height).')
    lines.append(f'const uint16_t {varname}[{len(frames)}][{width*height}] = {{')

    for fi, frame in enumerate(frames, start=1):
        lines.append(f'    // Frame {fi}')
        lines.append('    {')
        f = frame
        px = f.load()
        for y in range(height):
            row_vals: List[str] = []
            for x in range(width):
                p = px[x, y]
                # p is RGBA tuple
                r, g, b = rgba_to_rgb(bg, p)
                row_vals.append(f'color565({r}, {g}, {b})')
            rows = ', '.join(row_vals)
            lines.append(f'       /*{y}*/  {rows},')
        lines.append('    },')

    lines.append('};\n')
    lines.append(f'double {varname}_frame_time = {frame_time_s};\n')

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines))


def main(argv=None):
    p = argparse.ArgumentParser(description='Convert a GIF to a C header (color565 frames).')
    p.add_argument('input', help='input GIF file')
    p.add_argument('-o', '--output', help='output header file path (default: <input>.h)')
    p.add_argument('-n', '--name', help='variable base name')
    p.add_argument('--width', type=int, default=64, help='frame width (default 64)')
    p.add_argument('--height', type=int, default=64, help='frame height (default 64)')
    p.add_argument('--bg', nargs=3, type=int, metavar=('R','G','B'), help='background color for transparency (default 0 0 0)')
    args = p.parse_args(argv)

    in_path = Path(args.input)
    if not in_path.exists():
        print(f'Input file not found: {in_path}')
        return 2

    out_path = Path(args.output) if args.output else in_path.with_suffix('.h')
    # Default varname: use the input filename (stem) unless overridden with --name
    default_name = args.name if args.name else in_path.stem
    varname = sanitize_varname(default_name)
    size = (args.width, args.height)
    bg = tuple(args.bg) if args.bg else (0, 0, 0)

    frames, frame_time = extract_frames(in_path, size)
    write_c_header(out_path, varname, frames, frame_time, size[0], size[1], bg=bg)

    print(f'Wrote {out_path} — frames={len(frames)}, size={size[0]}x{size[1]}, frame_time={frame_time}s, var={varname}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())