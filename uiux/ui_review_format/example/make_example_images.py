#!/usr/bin/env python3
"""Write two tiny placeholder PNGs for the example manifest (stdlib only)."""
import struct
import zlib


def png(path, width, height, pixel):
    rows = b"".join(b"\x00" + b"".join(pixel(x, y) for x in range(width)) for y in range(height))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


def page(header_rgb):
    def pixel(x, y):
        if y < 40:
            return bytes(header_rgb)
        if 70 <= y < 90 and 30 <= x < 330 or 110 <= y < 220 and 30 <= x < 450:
            return b"\xd0\xd0\xd0"
        return b"\xfa\xfa\xfa"
    return pixel


png("before.png", 480, 300, page((120, 120, 120)))
png("after.png", 480, 300, page((31, 85, 168)))
