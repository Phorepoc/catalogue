# Copyright The Phorepoc Authors
# SPDX-License-Identifier: Apache-2.0
"""make_banner.py -- renders Catalogue's Home welcome banner: our own art, the Etesian design language
(https://language.etesian-design.com): the app tile's blue (#306EBD -> #15259A), soft light from the upper left, one
open catalogue in the tile glyph's cream (#F6F8ED -> #D0C9C6), its pages showing app tiles, at the right (the right
136/360 portrait, 176/640 landscape). No text in the picture: the app draws the welcome line beside it (phestore.loc).
Writes phestore_banner.mbm (bitmap 0 = portrait 360x130, 1 = landscape 640x130, 24 bpp; the app scales it to the
screen's width) and phestore_banner_preview.png. Run: py make_banner.py (needs Pillow)."""
import math
import os
import struct

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SS = 4                                  # supersampling
TOP, BOTTOM = (0x30, 0x6E, 0xBD), (0x15, 0x25, 0x9A)
CREAM = [(0xF6, 0xF8, 0xED), (0xEA, 0xE9, 0xE3), (0xD0, 0xC9, 0xC6)]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t + 0.5) for i in range(3))


def vgrad(w, h, c0, c1):
    g = Image.new("RGB", (1, h))
    for y in range(h):
        g.putpixel((0, y), lerp(c0, c1, y / max(1, h - 1)))
    return g.resize((w, h))


def glow(size, centre, radius, colour, alpha):
    layer = Image.new("RGBA", size, colour + (0,))
    d = ImageDraw.Draw(layer)
    x, y = centre
    d.ellipse((x - radius, y - radius, x + radius, y + radius), fill=colour + (alpha,))
    return layer.filter(ImageFilter.GaussianBlur(radius / 2))


TILES = [(0xF2, 0x8C, 0x3A), (0x3C, 0xB3, 0x71), (0x8E, 0x5B, 0xD9), (0x2B, 0xA8, 0xC9), (0xE8, 0x4E, 0x6A), (0xF4, 0xC4, 0x30)]
PAPER = (0xF4, 0xF2, 0xEA)
INK_DARK = (0x6A, 0x66, 0x64)
INK_LIGHT = (0xBE, 0xB8, 0xB3)
INK_BLUE = (0x30, 0x6E, 0xBD)


def ink(c, k=0.22):
    """a colour as printed ink: pulled toward the paper (lower contrast and saturation)"""
    grey = sum(c) / 3
    c = tuple(v + (grey - v) * 0.25 for v in c)                      # less saturated
    return tuple(int(v + (PAPER[i] - v) * k + 0.5) for i, v in enumerate(c))


def rrect(d, box, r, fill):
    d.rounded_rectangle(box, radius=r, fill=fill)


def page_flat(pw, ph, side):
    """one page drawn flat (pw x ph), its content laid out on the page margins. side -1 = left (a 2x3 tile grid),
    1 = right (three list rows and a button); both share the same margins and top/bottom lines"""
    img = Image.new("RGB", (pw, ph), PAPER)
    d = ImageDraw.Draw(img)
    mx, my = pw * 0.14, ph * 0.10                                    # outer margins (the same on both pages)
    gx = pw * 0.12                                                   # gutter between columns / items
    x0, x1, y0, y1 = mx, pw - mx, my, ph - my
    if side < 0:
        cols, rows = 2, 3
        t = min((x1 - x0 - gx * (cols - 1)) / cols, (y1 - y0 - gx * (rows - 1)) / rows)
        gy = (y1 - y0 - rows * t) / (rows - 1)
        gxx = (x1 - x0 - cols * t) / (cols - 1)
        n = 0
        for r in range(rows):
            for c in range(cols):
                bx, by = x0 + c * (t + gxx), y0 + r * (t + gy)
                rrect(d, (bx, by, bx + t, by + t), t * 0.24, ink(TILES[n]))
                g = t * 0.15
                d.ellipse((bx + t / 2 - g, by + t / 2 - g, bx + t / 2 + g, by + t / 2 + g), fill=ink((255, 255, 255), 0.12))
                n += 1
    else:
        bh = (y1 - y0) * 0.12                                        # the button's height, on the bottom margin line
        rows = 3
        area = (y1 - y0) - bh - gx
        t = min((area - gx * (rows - 1)) / rows, (x1 - x0) * 0.32)
        gy = (area - rows * t) / (rows - 1)
        for r in range(rows):
            by = y0 + r * (t + gy)
            rrect(d, (x0, by, x0 + t, by + t), t * 0.24, ink(TILES[(r + 3) % 6]))
            tx = x0 + t + gx * 0.7
            rrect(d, (tx, by + t * 0.14, x1, by + t * 0.40), t * 0.13, ink(INK_DARK))
            rrect(d, (tx, by + t * 0.60, tx + (x1 - tx) * 0.7, by + t * 0.82), t * 0.11, ink(INK_LIGHT))
        rrect(d, (x0, y1 - bh, x1, y1), bh / 2, ink(INK_BLUE))
    return img


def catalogue(size, cx, cy, s):
    """an open catalogue in a box of side s centred at (cx, cy). Each page is drawn flat, then laid on its curved plane
    column by column (the content follows the page), and the page's shading -- darker toward the spine -- goes over it"""
    W, H = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    pw, ph = s * 0.62, s * 0.80                                      # one page as seen (half the spread)
    top = cy - ph / 2
    dip = ph * 0.07                                                  # how far the page sinks into the gutter
    sag = ph * 0.035                                                 # the bottom edge's lesser curve
    thick = max(2, s * 0.03)                                         # the page block's thickness

    def x_of(side, u):                                               # u 0 = spine, 1 = outer edge; foreshortened near the spine
        return cx + side * pw * (0.6 * u + 0.4 * u * u)        # compressed toward the spine, where the page bends away

    def ys(u):
        k = (1 - u) ** 2.2
        return top + dip * k, top + ph + sag * k

    # the shadow under the book
    sh = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((cx - pw * 1.08, top + ph - s * 0.03, cx + pw * 1.08, top + ph + s * 0.13), fill=(5, 12, 60, 130))
    layer = Image.alpha_composite(layer, sh.filter(ImageFilter.GaussianBlur(s * 0.045)))
    d = ImageDraw.Draw(layer)
    # the cover, then the page block's thickness: a few page edges under each page's outer and bottom edges
    N = 48
    for side in (-1, 1):
        pts = [(x_of(side, i / N), ys(i / N)[1]) for i in range(N + 1)]
        cover = [(cx, ys(0)[0] + thick)] + [(x_of(side, 1) + side * thick * 1.2, ys(1)[0] + thick)] + \
                [(x + side * thick * 1.2 * (i / N), y + thick * 2.2) for i, (x, y) in reversed(list(enumerate(pts)))]
        d.polygon(cover, fill=(0x12, 0x20, 0x7C, 255))
        # the page block: one band under the outer and bottom edges, its paper edges as two tones
        for o, col in ((thick, (0xC8, 0xC2, 0xBB, 255)), (thick * 0.5, (0xE6, 0xE1, 0xD9, 255))):
            outer = [(x_of(side, i / N) + side * o * (i / N), ys(i / N)[1] + o) for i in range(N + 1)]
            outer.append((x_of(side, 1) + side * o, ys(1)[0] + o))
            inner = [(x_of(side, 1) - side * thick, ys(1)[0])] + [(x_of(side, i / N) - side * thick * (i / N), ys(i / N)[1] - thick) for i in range(N, -1, -1)]
            d.polygon(outer + inner, fill=col)
    # each page: flat content -> its curved plane, column by column, with the shading over the content
    FW, FH = int(pw * 1.6), int(ph * 1.6)                            # the flat page, a little oversampled
    for side in (-1, 1):
        flat = page_flat(FW, FH, side)
        xa, xb = int(min(x_of(side, 0), x_of(side, 1))), int(max(x_of(side, 0), x_of(side, 1)))
        cols = []
        for X in range(xa, xb + 1):
            # invert x_of for u (monotonic): bisection
            lo, hi = 0.0, 1.0
            for _ in range(22):
                m = (lo + hi) / 2
                if (x_of(side, m) - cx) * side < (X - cx) * side:
                    lo = m
                else:
                    hi = m
            cols.append((X, (lo + hi) / 2))
        for X, u in cols:
            y0, y1 = ys(u)
            hgt = int(math.ceil(y1)) - int(y0) + 1
            if hgt <= 0:
                continue
            src_x = min(FW - 1, int((u if side > 0 else 1 - u) * FW))
            strip = flat.crop((src_x, 0, src_x + 1, FH)).resize((1, hgt), Image.BILINEAR)
            # shading: darker toward the spine, a soft light band on the page's rise, slightly cooler on the right page
            shade = 0.70 + 0.30 * min(1, u * 3.2) ** 0.7
            if side > 0:
                shade *= 0.96
            shade = min(1.0, shade + 0.04 * max(0, 1 - abs(u - 0.35) * 4))
            px = strip.point(lambda v: int(v * shade))
            layer.paste(px.convert("RGBA"), (X, int(y0)))
    d = ImageDraw.Draw(layer)
    # the gutter: a thin dark fold
    d.line([(cx, ys(0)[0]), (cx, ys(0)[1])], fill=(0x8C, 0x85, 0x82, 255), width=max(1, int(s * 0.008)))
    return layer


def banner(w, h, art_w):
    """the band at w x h, the catalogue centred in the right art_w (pheui.cpp DrawBanner keeps the text left of it)"""
    W, H = w * SS, h * SS
    img = vgrad(W, H, TOP, BOTTOM).convert("RGBA")
    img = Image.alpha_composite(img, glow((W, H), (W * 0.12, -H * 0.2), H * 1.0, (0x5A, 0x96, 0xDC), 90))
    img = Image.alpha_composite(img, glow((W, H), (W * 0.55, H * 1.1), H * 0.8, (0x2C, 0x60, 0xB8), 70))
    s = H * 0.74
    cx, cy = W - art_w * SS / 2, H * 0.47
    img = Image.alpha_composite(img, glow((W, H), (cx, cy), s * 0.70, (0x6C, 0xA6, 0xE6), 100))
    rings = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rings)
    rd.ellipse((-W * 0.15, -H * 1.3, W * 0.55, H * 0.9), outline=(0x8C, 0xBC, 0xF0, 50), width=SS * 2)
    img = Image.alpha_composite(img, rings.filter(ImageFilter.GaussianBlur(SS)))
    img = Image.alpha_composite(img, catalogue((W, H), cx, cy, s))
    return img.convert("RGB").resize((w, h), Image.LANCZOS)


def uid_checksum(u1, u2, u3):
    def crc(data):
        c = 0
        for byte in data:
            c ^= byte << 8
            for _ in range(8):
                c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
        return c
    b = struct.pack("<3I", u1, u2, u3)
    even, odd = crc(b[0::2]), crc(b[1::2])
    return (odd << 16) | even


def mbm(images):
    blobs = []
    for img in images:
        w, h = img.size
        stride = (w * 3 + 3) & ~3
        data = bytearray()
        for y in range(h):
            row = bytearray()
            for x in range(w):
                r, g, b = img.getpixel((x, y))
                row += bytes((b, g, r))
            row += b"\0" * (stride - len(row))
            data += row
        blobs.append(struct.pack("<10i", 40 + len(data), 40, w, h, w * 15, h * 15, 24, 1, 0, 0) + bytes(data))
    off, offsets = 20, []
    for b in blobs:
        offsets.append(off)
        off += len(b)
    uids = (0x10000037, 0x10000042, 0)
    head = struct.pack("<5I", uids[0], uids[1], uids[2], uid_checksum(*uids), off)
    return head + b"".join(blobs) + struct.pack("<I", len(blobs)) + b"".join(struct.pack("<I", o) for o in offsets)


if __name__ == "__main__":
    p, l = banner(360, 130, 136), banner(640, 130, 176)
    with open(os.path.join(HERE, "phestore_banner.mbm"), "wb") as f:
        f.write(mbm([p, l]))
    prev = Image.new("RGB", (640, 270), (255, 255, 255))
    prev.paste(p, (0, 0))
    prev.paste(l, (0, 140))
    prev.save(os.path.join(HERE, "phestore_banner_preview.png"))
