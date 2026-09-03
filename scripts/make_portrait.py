#!/usr/bin/env python3

import argparse
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove


# =========================
# SETTINGS
# =========================

RAMP = " .`:-=+*cs#%@"

COLS = 100

CLAHE_CLIP = 3.0
GAMMA = 1.0
CURVE = 1.7

CROP_BOTTOM = 0.0
ROW_RATIO = 0.48

FG_LIGHT = "#6e7681"
FG_DARK = "#c9d1d9"

CHAR_W = 7.74
FONT_SIZE = 12.9
LINE_H = 15

ROW_DELAY = 0.09

FAMILY = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


# =========================
# IMAGE PROCESSING
# =========================

def prep(path, crop=None):
    """
    Remove the background, improve contrast,
    and prepare the image for ASCII conversion.
    """

    src = Image.open(path).convert("RGBA")

    if crop:
        src = src.crop(crop)

    cut = remove(src)

    alpha = np.array(cut.split()[-1])

    # Put subject on white background.
    white = Image.new(
        "RGBA",
        cut.size,
        (255, 255, 255, 255)
    )

    gray = np.array(
        Image.alpha_composite(
            white,
            cut
        ).convert("L")
    )

    # Smooth small skin details while preserving edges.
    gray = cv2.bilateralFilter(
        gray,
        11,
        50,
        50
    )

    # Improve local contrast.
    gray = cv2.createCLAHE(
        clipLimit=CLAHE_CLIP,
        tileGridSize=(8, 8)
    ).apply(gray)

    # Darkening curve.
    gray = (
        255.0 *
        (gray / 255.0) ** CURVE
    ).astype("uint8")

    # Force background to blank.
    gray[alpha < 20] = 255

    return Image.fromarray(gray)


# =========================
# ASCII CONVERSION
# =========================

def to_lines(img, cols=COLS, gamma=GAMMA):

    w, h = img.size

    if CROP_BOTTOM:
        img = img.crop(
            (
                0,
                0,
                w,
                int(h * (1 - CROP_BOTTOM))
            )
        )

    w, h = img.size

    rows = int(
        cols *
        (h / w) *
        ROW_RATIO
    )

    rows = max(rows, 1)

    img = img.resize(
        (cols, rows),
        Image.LANCZOS
    )

    px = list(img.getdata())

    n = len(RAMP)

    output = []

    for r in range(rows):

        line = ""

        for c in range(cols):

            brightness = px[
                r * cols + c
            ]

            value = (
                1 -
                brightness / 255.0
            ) ** gamma

            index = min(
                n - 1,
                int(value * n)
            )

            line += RAMP[index]

        output.append(
            line.rstrip()
        )

    # Remove empty rows from top.
    while output and not output[0].strip():
        output.pop(0)

    # Remove empty rows from bottom.
    while output and not output[-1].strip():
        output.pop()

    return output


# =========================
# SVG GENERATOR
# =========================

def build_svg(lines, cols=COLS):

    pad = 14

    width = int(
        cols * CHAR_W +
        pad * 2
    )

    height = (
        len(lines) * LINE_H +
        pad * 2
    )

    svg = []

    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" '
        f'height="{height}" '
        f'viewBox="0 0 {width} {height}" '
        f'font-family="{FAMILY}">'
    )

    svg.append(
        f'<style>'
        f'.a{{fill:{FG_LIGHT}}}'
        f'@media(prefers-color-scheme:dark)'
        f'{{.a{{fill:{FG_DARK}}}}}'
        f'</style>'
    )

    for i, line in enumerate(lines):

        y = pad + i * LINE_H

        begin = f"{i * ROW_DELAY:.2f}s"
        end = f"{(i + 1) * ROW_DELAY:.2f}s"

        line_width = max(
            len(line),
            1
        ) * CHAR_W

        safe = (
            line
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        # Animated clipping rectangle.
        svg.append(
            f'<clipPath id="c{i}">'
            f'<rect '
            f'x="{pad}" '
            f'y="{y}" '
            f'height="{LINE_H}" '
            f'width="0">'
            f'<animate '
            f'attributeName="width" '
            f'from="0" '
            f'to="{line_width:.1f}" '
            f'begin="{begin}" '
            f'dur="{ROW_DELAY}s" '
            f'fill="freeze"/>'
            f'</rect>'
            f'</clipPath>'
        )

        # ASCII row.
        svg.append(
            f'<g clip-path="url(#c{i})">'
            f'<text '
            f'xml:space="preserve" '
            f'x="{pad}" '
            f'y="{y + 11.2:.1f}" '
            f'class="a" '
            f'font-size="{FONT_SIZE}">'
            f'{safe}'
            f'</text>'
            f'</g>'
        )

        # Cursor animation.
        svg.append(
            f'<rect '
            f'y="{y + 1}" '
            f'width="6" '
            f'height="12" '
            f'class="a" '
            f'opacity="0">'
            f'<animate '
            f'attributeName="x" '
            f'from="{pad}" '
            f'to="{pad + line_width:.1f}" '
            f'begin="{begin}" '
            f'dur="{ROW_DELAY}s" '
            f'fill="freeze"/>'
            f'<set '
            f'attributeName="opacity" '
            f'to="0.8" '
            f'begin="{begin}"/>'
            f'<set '
            f'attributeName="opacity" '
            f'to="0" '
            f'begin="{end}"/>'
            f'</rect>'
        )

    svg.append("</svg>")

    return "".join(svg)


# =========================
# MAIN
# =========================

def main():

    parser = argparse.ArgumentParser(
        description="Generate an animated ASCII portrait SVG."
    )

    parser.add_argument(
        "photo",
        help="Input photo"
    )

    parser.add_argument(
        "out",
        nargs="?",
        default="ascii.svg",
        help="Output SVG"
    )

    parser.add_argument(
        "--crop",
        help="left,top,right,bottom"
    )

    parser.add_argument(
        "--cols",
        type=int,
        default=COLS
    )

    parser.add_argument(
        "--preview",
        action="store_true"
    )

    args = parser.parse_args()

    crop = None

    if args.crop:

        parts = [
            int(v)
            for v in args.crop.split(",")
        ]

        if len(parts) != 4:
            sys.exit(
                "--crop needs four numbers: "
                "left,top,right,bottom"
            )

        crop = tuple(parts)

    image = prep(
        args.photo,
        crop
    )

    lines = to_lines(
        image,
        cols=args.cols
    )

    if args.preview:
        print()
        print("\n".join(lines))
        print()

    with open(
        args.out,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            build_svg(
                lines,
                cols=args.cols
            )
        )

    print(
        f"wrote {args.out} — "
        f"{len(lines)} rows, "
        f"{args.cols} columns"
    )


if __name__ == "__main__":
    main()
