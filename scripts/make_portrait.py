#!/usr/bin/env python3

from PIL import Image, ImageEnhance, ImageFilter
import argparse
import html

# Empty → dark/dense
RAMP = " .:-=+*#%@"

COLS = 90
ROW_RATIO = 0.48

FONT_SIZE = 13
LINE_HEIGHT = 15
CHAR_WIDTH = 7.8

DARK = "#c9d1d9"


def prepare(path, crop=None):
    image = Image.open(path).convert("RGB")

    if crop:
        image = image.crop(crop)

    # Grayscale
    image = image.convert("L")

    # Improve facial contrast
    image = ImageEnhance.Contrast(image).enhance(1.6)

    # Slight sharpening
    image = image.filter(ImageFilter.UnsharpMask(
        radius=1.2,
        percent=130,
        threshold=3
    ))

    return image


def ascii_lines(image, cols):
    width, height = image.size

    rows = max(
        1,
        int(cols * (height / width) * ROW_RATIO)
    )

    image = image.resize(
        (cols, rows),
        Image.Resampling.LANCZOS
    )

    pixels = list(image.getdata())

    result = []

    for y in range(rows):
        line = []

        for x in range(cols):
            brightness = pixels[y * cols + x]

            # Darker pixels → denser characters
            darkness = 1 - brightness / 255

            index = int(
                darkness * (len(RAMP) - 1)
            )

            line.append(RAMP[index])

        result.append("".join(line).rstrip())

    # Remove empty rows around portrait
    while result and not result[0].strip():
        result.pop(0)

    while result and not result[-1].strip():
        result.pop()

    return result


def create_svg(lines, cols):
    padding = 14

    width = int(
        cols * CHAR_WIDTH + padding * 2
    )

    height = int(
        len(lines) * LINE_HEIGHT + padding * 2
    )

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" '
        f'height="{height}" '
        f'viewBox="0 0 {width} {height}">',

        '<rect width="100%" height="100%" '
        'fill="#000000"/>',

        f'<g fill="{DARK}" '
        'font-family="ui-monospace, '
        'SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="{FONT_SIZE}px">'
    ]

    for row, line in enumerate(lines):

        y = padding + row * LINE_HEIGHT + FONT_SIZE

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
        "photo"
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
            int(x)
            for x in args.crop.split(",")
        ]

        if len(values) != 4:
            raise SystemExit(
                "--crop needs: left,top,right,bottom"
            )

        crop = tuple(values)

    image = prepare(
        args.photo,
        crop
    )

    lines = ascii_lines(
        image,
        args.cols
    )

    svg = create_svg(
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
        f"Generated {args.output} "
        f"({args.cols} columns × {len(lines)} rows)"
    )


if __name__ == "__main__":
    main()
