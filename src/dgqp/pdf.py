"""Minimal, dependency-free PDF writer with text and one embedded PNG image.

Why this exists
---------------
The offline sandbox has no reportlab/Pillow. This module writes a valid PDF
using only the standard library: multiple text pages (Helvetica) and an RGB
image page that embeds the published icon architecture PNG as a FlateDecode
image XObject. It decodes PNG color type 2, bit depth 8 (the published figure's
format) using ``zlib``; other PNG variants raise, so we never silently ship a
blank figure.

This is deliberately small: it covers exactly what ``make report`` needs. It is
not a general PDF toolkit.
"""

from __future__ import annotations

import struct
import zlib


class PngError(ValueError):
    pass


def decode_png_rgb(data: bytes) -> tuple[int, int, bytes]:
    """Decode an 8-bit RGB (color type 2) PNG to raw RGB bytes.

    Returns ``(width, height, rgb_bytes)``. Raises :class:`PngError` for any
    unsupported variant so the caller can fail closed.
    """
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise PngError("not a PNG")
    pos = 8
    width = height = bit_depth = color_type = None
    idat = bytearray()
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk[:10])
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            break
        pos += 12 + length

    if bit_depth != 8 or color_type != 2:
        raise PngError(f"unsupported PNG (bit_depth={bit_depth}, color_type={color_type})")

    raw = zlib.decompress(bytes(idat))
    channels = 3
    stride = width * channels
    out = bytearray(height * stride)
    prev = bytearray(stride)
    src = 0
    for y in range(height):
        ftype = raw[src]
        src += 1
        line = bytearray(raw[src:src + stride])
        src += stride
        _unfilter(ftype, line, prev, channels)
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return width, height, bytes(out)


def _unfilter(ftype: int, line: bytearray, prev: bytearray, bpp: int) -> None:
    if ftype == 0:
        return
    for i in range(len(line)):
        a = line[i - bpp] if i >= bpp else 0
        b = prev[i]
        c = prev[i - bpp] if i >= bpp else 0
        x = line[i]
        if ftype == 1:
            line[i] = (x + a) & 0xFF
        elif ftype == 2:
            line[i] = (x + b) & 0xFF
        elif ftype == 3:
            line[i] = (x + ((a + b) >> 1)) & 0xFF
        elif ftype == 4:
            line[i] = (x + _paeth(a, b, c)) & 0xFF
        else:
            raise PngError(f"unknown PNG filter {ftype}")


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


# --- PDF assembly ---------------------------------------------------------

PAGE_W, PAGE_H = 595, 842  # A4 points
MARGIN = 54


def _esc(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


class PdfBuilder:
    def __init__(self) -> None:
        self._objects: list[bytes] = []
        self._page_refs: list[int] = []
        self._font_obj = None

    def _add(self, body: bytes) -> int:
        self._objects.append(body)
        return len(self._objects)

    def add_text_page(self, lines: list[str]) -> None:
        font = self._ensure_font()
        content = ["BT", f"/F1 11 Tf", "13 TL", f"1 0 0 1 {MARGIN} {PAGE_H - MARGIN} Tm"]
        for raw in lines:
            for wrapped in _wrap(raw, 95):
                content.append(f"({_esc(wrapped)}) Tj T*")
        content.append("ET")
        stream = "\n".join(content).encode("latin-1", "replace")
        content_obj = self._add(_stream_obj(stream))
        page_obj = self._add(
            (f"<< /Type /Page /Parent 0 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
             f"/Resources << /Font << /F1 {font} 0 R >> >> "
             f"/Contents {content_obj} 0 R >>").encode("latin-1")
        )
        self._page_refs.append(page_obj)

    def add_image_page(self, width: int, height: int, rgb: bytes, caption: str) -> None:
        font = self._ensure_font()
        compressed = zlib.compress(rgb, 9)
        img_header = (
            f"<< /Type /XObject /Subtype /Image /Width {width} /Height {height} "
            f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode "
            f"/Length {len(compressed)} >>"
        ).encode("latin-1")
        img_obj = self._add(img_header + b"\nstream\n" + compressed + b"\nendstream")

        # Fit the image to the page width, preserving aspect ratio.
        draw_w = PAGE_W - 2 * MARGIN
        draw_h = draw_w * height / width
        if draw_h > PAGE_H - 3 * MARGIN:
            draw_h = PAGE_H - 3 * MARGIN
            draw_w = draw_h * width / height
        x = (PAGE_W - draw_w) / 2
        y = PAGE_H - MARGIN - draw_h
        content = (
            f"q {draw_w:.2f} 0 0 {draw_h:.2f} {x:.2f} {y:.2f} cm /Im0 Do Q\n"
            f"BT /F1 10 Tf 1 0 0 1 {MARGIN} {y - 18:.2f} Tm ({_esc(caption)}) Tj ET"
        ).encode("latin-1")
        content_obj = self._add(_stream_obj(content))
        page_obj = self._add(
            (f"<< /Type /Page /Parent 0 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
             f"/Resources << /Font << /F1 {font} 0 R >> "
             f"/XObject << /Im0 {img_obj} 0 R >> >> "
             f"/Contents {content_obj} 0 R >>").encode("latin-1")
        )
        self._page_refs.append(page_obj)

    def _ensure_font(self) -> int:
        if self._font_obj is None:
            self._font_obj = self._add(
                b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
            )
        return self._font_obj

    def build(self) -> bytes:
        pages_obj = self._add(b"")  # placeholder, filled below
        kids = " ".join(f"{ref} 0 R" for ref in self._page_refs)
        self._objects[pages_obj - 1] = (
            f"<< /Type /Pages /Count {len(self._page_refs)} /Kids [{kids}] >>"
        ).encode("latin-1")
        catalog_obj = self._add(f"<< /Type /Catalog /Pages {pages_obj} 0 R >>".encode("latin-1"))

        # Fix /Parent references to point at the pages object.
        for ref in self._page_refs:
            self._objects[ref - 1] = self._objects[ref - 1].replace(
                b"/Parent 0 0 R", f"/Parent {pages_obj} 0 R".encode("latin-1")
            )

        out = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for i, body in enumerate(self._objects, start=1):
            offsets.append(len(out))
            out += f"{i} 0 obj\n".encode("latin-1") + body + b"\nendobj\n"
        xref_pos = len(out)
        n = len(self._objects) + 1
        out += f"xref\n0 {n}\n".encode("latin-1")
        out += b"0000000000 65535 f \n"
        for off in offsets[1:]:
            out += f"{off:010d} 00000 n \n".encode("latin-1")
        out += (f"trailer\n<< /Size {n} /Root {catalog_obj} 0 R >>\n"
                f"startxref\n{xref_pos}\n%%EOF").encode("latin-1")
        return bytes(out)


def _stream_obj(stream: bytes) -> bytes:
    return (f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1")
            + stream + b"\nendstream")


def _wrap(text: str, width: int) -> list[str]:
    if not text:
        return [""]
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        if len(cur) + len(word) + 1 > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    lines.append(cur)
    return lines
