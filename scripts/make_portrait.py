from PIL import Image
import sys
import html

CHARS = ":+#@"

def make_portrait(input_file, output_file, width=100):
    image = Image.open(input_file).convert("L")

    # Preserve the aspect ratio while compensating for terminal
    # characters being taller than they are wide.
    aspect = image.height / image.width
    height = max(1, int(width * aspect * 0.48))

    image = image.resize((width, height))

    pixels = list(image.getdata())

    rows = []

    for y in range(height):
        row = []

        for x in range(width):
            value = pixels[y * width + x]

            # Dark -> light character ramp
            index = int(value / 256 * len(CHARS))

            if index >= len(CHARS):
                index = len(CHARS) - 1

            row.append(CHARS[index])

        rows.append("".join(row))

    svg_width = width * 10
    line_height = 11
    svg_height = height * line_height

    text_rows = []

    for i, row in enumerate(rows):
        escaped = html.escape(row)

        text_rows.append(
            f'<text x="0" y="{(i + 1) * line_height}" '
            f'font-family="JetBrains Mono, monospace" '
            f'font-size="10" '
            f'xml:space="preserve">{escaped}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
    width="{svg_width}"
    height="{svg_height}"
    viewBox="0 0 {svg_width} {svg_height}">
    <rect width="100%" height="100%" fill="#000000"/>
    <g fill="#ffffff">
        {"".join(text_rows)}
    </g>
</svg>
'''

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"Created {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python make_portrait.py input.jpg output.svg")
        sys.exit(1)

    make_portrait(sys.argv[1], sys.argv[2])
