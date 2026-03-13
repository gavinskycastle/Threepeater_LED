#!/usr/bin/env python3
"""
gif_to_header.py

Convert a GIF file into a C header that embeds the decoded frames as
an array of Color(r,g,b) values (matching the style used in
`test_pattern.h` in this workspace).

Usage:
    python gif_to_header.py input.gif -o output.h

By default the script decodes all frames, emits a static 16-bit
Color(...) helper, a `uint16_t dancing_frames[frames][width*height]`
array, and a `double dancing_frame_time` (seconds per frame).

Requires Pillow to decode GIF frames.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional
from PIL import Image, ImageSequence


def sanitize_varname(name: str) -> str:
    # keep only alnum and underscore, replace others with underscore
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


def format_bytes_c(data: bytes, per_line: int = 12, indent: str = '\t') -> str:
    hexs = [f"0x{b:02x}" for b in data]
    lines = []
    for i in range(0, len(hexs), per_line):
        chunk = hexs[i : i + per_line]
        lines.append(indent + ','.join(chunk) + ',')
    return '\n'.join(lines)


def detect_gif_info(path: Path) -> tuple[int, int, int]:
    # returns (width, height, n_frames)
    try:
        with Image.open(path) as img:
            w, h = img.size
            # n_frames attribute available for PIL >= 4.3
            n = getattr(img, 'n_frames', None)
            if n is None:
                # fallback: iterate
                n = sum(1 for _ in ImageSequence.Iterator(img))
            return (w, h, int(n))
    except Exception:
        return (0, 0, 0)


def build_frames_header(varname: str, frames_pixels: list[list[tuple[int,int,int]]], width: int, height: int, frame_time_s: float) -> str:
    # Builds a header in the same style as `test_pattern.h`:
    # - static uint16_t Color(uint8_t r, uint8_t g, uint8_t b) { ... }
    # - uint16_t dancing_frames[<n>][width*height] = { ... }
    # - double dancing_frame_time = <seconds>;
    n_frames = len(frames_pixels)
    header_lines: list[str] = []
    header_lines.append('static uint16_t Color(uint8_t r, uint8_t g, uint8_t b) {')
    # convert 8-bit per channel RGB into 16-bit RGB565 (R:5,G:6,B:5)
    # use masking/shifts so callers can pass 0-255 values as seen in examples
    header_lines.append('  return (uint16_t)(((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3));')
    header_lines.append('}\n')

    header_lines.append(f'uint16_t {varname}[{n_frames}][{width*height}] = {{')
    for fi, frame in enumerate(frames_pixels, start=1):
        header_lines.append(f'    // Frame {fi}')
        header_lines.append('    {')
        # print rows; each row is width entries, label comment /*row*/
        for row in range(height):
            row_idx = row
            start = row * width
            end = start + width
            entries = frame[start:end]
            entry_texts = [f'Color({r}, {g}, {b})' for (r,g,b) in entries]
            # join with comma+space, put 16 entries per line similar to example formatting
            line = '       /*%d*/  %s,' % (row_idx, ', '.join(entry_texts))
            header_lines.append(line)
        header_lines.append('    },')
    header_lines.append('};\n')
    header_lines.append(f'double dancing_frame_time = {frame_time_s:.6f}; // seconds per frame')
    return '\n'.join(header_lines)


def main(argv=None):
    p = argparse.ArgumentParser(description='Decode a GIF and emit a C header with dancing_frames array and dancing_frame_time.')
    p.add_argument('input', help='input GIF file path')
    p.add_argument('-o', '--output', help='output header file path (default: <input>.h)')
    p.add_argument('-n', '--name', help='array variable name to use in the header (default: dancing_frames)', default='dancing_frames')
    p.add_argument('--assume-size', nargs=2, metavar=('W', 'H'), type=int, help='assume the GIF dimensions (overrides detection)')
    p.add_argument('--no-resize', dest='no_resize', action='store_true', help='do not resize frames; fail if sizes do not match')
    p.add_argument('--bpp', type=int, default=16, help='bits per pixel to print in the header comment (unused)')
    args = p.parse_args(argv)

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"Input file not found: {in_path}")
        return 2

    out_path = Path(args.output) if args.output else in_path.with_suffix('.h')
    varname = args.name or 'dancing_frames'

    # decode frames using Pillow
    try:
        img = Image.open(in_path)
    except Exception as e:
        print(f"Failed to open image with Pillow: {e}")
        return 2

    detected_w, detected_h = img.size
    frames_pixels: list[list[tuple[int,int,int]]] = []
    durations_ms: list[int] = []

    # accumulate frames onto a base image to handle partial-frame GIFs
    base = Image.new('RGBA', img.size)
    for frame in ImageSequence.Iterator(img):
        duration = frame.info.get('duration', 100)  # ms
        durations_ms.append(duration)
        frame_rgba = frame.convert('RGBA')
        # paste with alpha to composite correctly
        base.paste(frame_rgba, (0,0), frame_rgba)
        rgb = base.convert('RGB')
        # optionally resize
        if args.assume_size:
            w, h = args.assume_size
            if (w, h) != rgb.size:
                if args.no_resize:
                    raise RuntimeError(f"Frame size {rgb.size} does not match assumed size {(w,h)} and --no-resize set")
                rgb = rgb.resize((w, h), resample=Image.NEAREST)
        w, h = rgb.size
        pixels = list(rgb.getdata())
        frames_pixels.append(pixels)

    # choose final width/height
    if args.assume_size:
        width, height = args.assume_size
    else:
        width, height = detected_w, detected_h

    # frame time: use the first non-zero duration or average
    frame_time_ms = next((d for d in durations_ms if d and d>0), durations_ms[0] if durations_ms else 100)
    frame_time_s = frame_time_ms / 1000.0

    header_text = build_frames_header(varname, frames_pixels, width, height, frame_time_s)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(header_text)

    print(f"Wrote frames header to {out_path} ({len(frames_pixels)} frames, {width}x{height} each)")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
