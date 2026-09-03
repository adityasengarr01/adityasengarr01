#!/usr/bin/env python3

from PIL import Image, ImageOps, ImageEnhance
import argparse
import html

# Dark -> light
RAMP = " .:-=+*#%@"

COLS = 100
ROW_RATIO = 0.48

FONT_SIZE = 12
LINE_H = 14
CHAR_W = 7.2

FG = "#c9d1d9"


def prepare_image(path, crop=None):
    img = Image.open(path).convert("RGB")

    if crop:
        img = img.crop(crop)

    # Grayscale
    img = ImageOps.grayscale(img)

    # Improve contrast
    img = ImageEnhance.Contrast(img).enhance(1.35)

    # Slightly sharpen
    img = ImageEnhance.Sharpness(img).enhance(1.25)

    return img


def image_to_ascii(img, cols=COLS):
    width, height = img.size

    rows = max(
        1,
        int(cols * (height / width) * ROW_RATIO)
    )

    img = img.resize((cols, rows), Image.Resampling.LANCZOS)

    pixels = list(img.getdata())

    lines = []

    for y in range(rows):
        line = ""

        for x in range(cols):
            brightness = pixels[y * cols + x]

            # Dark pixels -> dense characters
            index = int(
                (1 - brightness / 255) * (len(RAMP) - 1)
            )

            line += RAMP[index]

        lines.append(line.rstrip())

    # Remove completely empty rows
    while lines and not lines[0].strip():
        lines.pop(0)

    while lines and not lines[-1].strip():
        lines.pop()

    return lines


def build_svg(lines, cols=COLS):
    padding = 18

    width = int(cols * CHAR_W + padding * 2)
    height = int(len(lines) * LINE_H + padding * 2)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',

        '<rect width="100%" height="100%" fill="#000000"/>',

        f'<g fill="{FG}" '
        f'font-family="JetBrains Mono, '
        f'SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="{FONT_SIZE}px">'
    ]

    for row, line in enumerate(lines):

        y = padding + row * LINE_H + FONT_SIZE

        safe = html.escape(line)

        svg.append(
            f'<text x="{padding}" y="{y}" '
            f'xml:space="preserve">{safe}</text>'
        )

    svg.append("</g>")
    svg.append("</svg>")

    return "\n".join(svg)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "photo",
        help="Input photo"
    )

    parser.add_argument(
        "output",
        nargs="?",
        default="ascii.svg"
    )

    parser.add_argument(
        "--cols",
        type=int,
        default=COLS
    )

    parser.add_argument(
        "--crop",
        help="left,top,right,bottom"
    )

    args = parser.parse_args()

    crop = None

    if args.crop:
        values = [
            int(value)
            for value in args.crop.split(",")
        ]

        if len(values) != 4:
            raise SystemExit(
                "--crop requires: left,top,right,bottom"
            )

        crop = tuple(values)

    image = prepare_image(
        args.photo,
        crop
    )

    lines = image_to_ascii(
        image,
        args.cols
    )

    svg = build_svg(
        lines,
        args.cols
    )

    with open(
        args.output,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(svg)

    print(
        f"Generated {args.output}: "
        f"{len(lines)} rows × {args.cols} columns"
    )


if __name__ == "__main__":
    main()
