"""Renders the Dsk icon: "dsk" in a heavy grotesk over a dot-matrix bar (five of seven cells lit lime),
on the same tile as Dwn, Tag and Lut.
    python assets/make_icon.py        (writes icon.png, icon.ico, AppIcon.icns and docs/icon-256.png)
Needs Pillow and the Inter Display Black font (https://rsms.me/inter/); pass a font path to override.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = sys.argv[1] if len(sys.argv) > 1 else "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
LIME = (204, 255, 77, 255)
S = 1024
X0, Y0, X1, Y1 = 70, 67, 954, 951   # tile bounds, same as the Tag icon
R = 200


def tile():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((X0, Y0, X1, Y1), R, fill=255)
    grad = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(grad)
    for y in range(S):
        t = min(1, max(0, (y - Y0) / (Y1 - Y0)))
        c = round(43 + (18 - 43) * t)
        d.line([(0, y), (S, y)], fill=(c, c, c + 2, 255))
    img.paste(grad, (0, 0), mask)
    ImageDraw.Draw(img).rounded_rectangle((X0, Y0, X1, Y1), R, outline=(255, 255, 255, 36), width=4)
    # soft drop shadow underneath
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((X0, Y0 + 14, X1, Y1 + 14), R, fill=(0, 0, 0, 90))
    from PIL import ImageFilter

    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    return Image.alpha_composite(shadow, img)


def mark(img):
    from PIL import ImageFilter

    size = 400
    font = ImageFont.truetype(FONT, size)
    kern = -0.055 * size
    widths = [font.getlength(ch) for ch in "dsk"]
    total = sum(widths) + kern * 2
    x0 = (S - total) / 2
    asc, _ = font.getmetrics()
    baseline = (Y0 + Y1) / 2 + size * 0.22
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x = x0
    for ch, w in zip("dsk", widths):
        d.text((x, baseline - asc), ch, font=font, fill=(255, 255, 255, 242))
        x += w + kern
    img = Image.alpha_composite(img, layer)
    # the bar: seven square cells under the letters
    cell = 0.13 * size
    y = baseline + 0.12 * size
    span = total - 0.04 * size
    step = (span - cell) / 6
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cells = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd, cd = ImageDraw.Draw(glow), ImageDraw.Draw(cells)
    for i in range(7):
        cx = x0 + 0.01 * size + i * step
        box = (cx, y, cx + cell, y + cell)
        if i < 5:
            gd.rounded_rectangle(box, cell * 0.2, fill=(204, 255, 77, 150))
            cd.rounded_rectangle(box, cell * 0.2, fill=LIME)
        else:
            cd.rounded_rectangle(box, cell * 0.2, fill=(255, 255, 255, 52))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(16)))
    return Image.alpha_composite(img, cells)


img = mark(tile())
img.save(os.path.join(HERE, "icon.png"))
img.resize((256, 256), Image.LANCZOS).save(os.path.join(HERE, "..", "docs", "icon-256.png"))
img.save(os.path.join(HERE, "icon.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
img.save(os.path.join(HERE, "AppIcon.icns"))
print("icons written")
