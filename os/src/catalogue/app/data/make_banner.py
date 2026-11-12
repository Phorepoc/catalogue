# Copyright The Phorepoc Authors
# SPDX-License-Identifier: Apache-2.0
"""make_banner.py -- renders Catalogue's Home welcome banner: our own art, the Etesian design language
(https://language.etesian-design.com): the app tile's blue (#306EBD -> #15259A), soft light from the upper left, one
3D shopping basket in the tile glyph's cream (#F6F8ED -> #D0C9C6), lit from above. No text: the banner is Home's title.
Writes phestore_banner.mbm (bitmap 0 = portrait 360x130, 1 = landscape 640x130, 24 bpp; the app scales it to the
screen's width) and phestore_banner_preview.png. Run: py make_banner.py (needs Pillow)."""
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


def basket(size, cx, cy, s):
    """the basket in a box of side s centred at (cx, cy): handle, rim, tapered body with a shaded right side, slats"""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    top, bottom = cy - s * 0.10, cy + s * 0.46
    hw_top, hw_bot = s * 0.50, s * 0.36
    rim = s * 0.11
    # the shadow it casts on the banner
    sh = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((cx - hw_bot * 1.25, bottom - rim * 0.3, cx + hw_bot * 1.35, bottom + rim * 1.4), fill=(5, 12, 60, 120))
    layer = Image.alpha_composite(layer, sh.filter(ImageFilter.GaussianBlur(s * 0.05)))
    d = ImageDraw.Draw(layer)
    # the handle: an arch behind the rim, a darker core and a lit upper edge
    hw = s * 0.34
    box = (cx - hw, top - s * 0.52, cx + hw, top + s * 0.36)
    d.arc(box, 180, 360, fill=(0xB9, 0xB1, 0xAD, 255), width=int(s * 0.075))
    d.arc((box[0], box[1] - s * 0.012, box[2], box[3] - s * 0.012), 185, 355, fill=CREAM[0] + (255,), width=int(s * 0.03))
    # the inside, seen over the rim
    d.ellipse((cx - hw_top, top - rim, cx + hw_top, top + rim), fill=(0x8F, 0x88, 0x86, 255))
    # the body: a lit left, a shaded right third; vertical cream gradient
    rows = int(bottom - top)
    for i in range(rows + 1):
        t = i / max(1, rows)
        half = hw_top - (hw_top - hw_bot) * t
        y = top + i
        split = cx + half * 0.35
        d.line((cx - half, y, split, y), fill=lerp(CREAM[0], CREAM[2], t) + (255,))
        d.line((split, y, cx + half, y), fill=lerp((0xC8, 0xC0, 0xBC), (0x9E, 0x96, 0x93), t) + (255,))
    # the rounded bottom
    d.chord((cx - hw_bot, bottom - rim * 0.8, cx + hw_bot, bottom + rim * 0.8), 0, 180, fill=(0xA8, 0x9F, 0x9C, 255))
    # slats: grooves following the taper, and two weave bands across
    for k in (-2, -1, 0, 1, 2):
        d.line((cx + k * hw_top / 3, top + rim, cx + k * hw_bot / 3, bottom), fill=(0xAE, 0xA6, 0xA3, 255), width=max(1, int(s * 0.018)))
    for f in (0.38, 0.70):
        y = top + (bottom - top) * f
        half = hw_top - (hw_top - hw_bot) * f
        d.arc((cx - half, y - rim * 0.7, cx + half, y + rim * 0.7), 0, 180, fill=(0xB4, 0xAC, 0xA8, 255), width=max(1, int(s * 0.02)))
    # the rim: a cream band, its front lip catching the light
    d.ellipse((cx - hw_top, top - rim, cx + hw_top, top + rim), outline=CREAM[1] + (255,), width=int(s * 0.06))
    d.arc((cx - hw_top, top - rim, cx + hw_top, top + rim), 10, 170, fill=(255, 255, 255, 255), width=max(1, int(s * 0.02)))
    return layer


def banner(w, h):
    W, H = w * SS, h * SS
    img = vgrad(W, H, TOP, BOTTOM).convert("RGBA")
    img = Image.alpha_composite(img, glow((W, H), (W * 0.12, -H * 0.2), H * 1.0, (0x5A, 0x96, 0xDC), 90))
    img = Image.alpha_composite(img, glow((W, H), (W * 0.55, H * 1.1), H * 0.8, (0x2C, 0x60, 0xB8), 70))
    s = H * 0.72
    cx, cy = W - s * 0.75, H * 0.52
    img = Image.alpha_composite(img, glow((W, H), (cx, cy), s * 0.75, (0x6C, 0xA6, 0xE6), 110))
    # two faint light rings (the swirl of the original idea, kept abstract)
    rings = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rings)
    rd.ellipse((-W * 0.15, -H * 1.3, W * 0.55, H * 0.9), outline=(0x8C, 0xBC, 0xF0, 60), width=SS * 2)
    rd.ellipse((W * 0.30, H * 0.35, W * 0.30 + H * 1.6, H * 1.95), outline=(0x8C, 0xBC, 0xF0, 45), width=SS * 2)
    img = Image.alpha_composite(img, rings.filter(ImageFilter.GaussianBlur(SS)))
    img = Image.alpha_composite(img, basket((W, H), cx, cy, s))
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
    p, l = banner(360, 130), banner(640, 130)
    with open(os.path.join(HERE, "phestore_banner.mbm"), "wb") as f:
        f.write(mbm([p, l]))
    prev = Image.new("RGB", (640, 270), (255, 255, 255))
    prev.paste(p, (0, 0))
    prev.paste(l, (0, 140))
    prev.save(os.path.join(HERE, "phestore_banner_preview.png"))
