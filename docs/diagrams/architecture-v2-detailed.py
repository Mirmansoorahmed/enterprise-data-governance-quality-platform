#!/usr/bin/env python3
"""Data Governance Framework Automation — reference architecture.

Hand-authored SVG, generated from this script so every coordinate is editable.
Icons are inlined from ./icons (see icons/SOURCES.md for source + licence).

    python3 architecture.py          # writes architecture.svg and architecture.png

PNG export uses headless Google Chrome (Inter variable font, 2x device scale).
"""
from __future__ import annotations

import math
import re
import subprocess
import sys
from pathlib import Path

from lxml import etree
from PIL import ImageFont

HERE = Path(__file__).resolve().parent
ICONS = HERE / "icons"
W, H = 2200, 1480
FONT_FILE = "/usr/share/fonts/truetype/sand-box/google/Inter/Inter-VariableFont_opsz,wght.ttf"

# ---------------------------------------------------------------- palette
NAVY = "#0F2A47"
NAVY2 = "#1F3A5F"
INK = "#1B2B3C"
GREY = "#5B6B7C"
GREY2 = "#8A99A8"
LINE = "#C9D3DD"
ZONE = "#F6F8FA"
CARD = "#FFFFFF"
TEAL = "#0B8A8A"
TEAL_L = "#E3F3F2"
TEAL_LINE = "#9FCFCB"
GREEN = "#047857"
GREEN_L = "#DCFCE7"
GREEN_LINE = "#6EE7B7"
AMBER = "#A86A12"
AMBER_L = "#FBF1E1"
BLUE = "#1D4ED8"
BLUE_L = "#EFF6FF"
RED = "#C0392B"
RED_L = "#FCF1F0"
FONT = "Inter, 'Segoe UI', Helvetica, Arial, sans-serif"

SI_HEX = {
    "python": "#3776AB",
    "dbt": "#FF694B",
    "docker": "#2496ED",
    "sap": "#0FAAFF",
    "microsoft": "#737373",
}

out: list[str] = []
warnings: list[str] = []
_uid = [0]
_fonts: dict = {}


def text_w(s: str, size: float, weight: int = 400) -> float:
    key = (size, weight)
    if key not in _fonts:
        f = ImageFont.truetype(FONT_FILE, 100)
        f.set_variation_by_axes([14, weight])
        _fonts[key] = f
    return _fonts[key].getlength(s) * size / 100


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=13, weight=400, fill=INK, anchor="start", maxw=None, italic=False, ls=0, halo=False):
    if maxw is not None:
        w = text_w(s, size, weight)
        if w > maxw + 0.5:
            warnings.append(f"text too wide ({w:.0f}>{maxw:.0f}): {s!r}")
    style = ' font-style="italic"' if italic else ""
    lsp = f' letter-spacing="{ls}"' if ls else ""
    if halo:
        lsp += ' stroke="#FFFFFF" stroke-width="5" stroke-linejoin="round" paint-order="stroke"'
    out.append(
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}"{style}{lsp}>{esc(s)}</text>'
    )


def rect(x, y, w, h, fill=CARD, stroke=LINE, sw=1, rx=6, dash=None, extra=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{sw}"{d}{extra}/>'
    )


def chip(x, y, s, fg, bg, size=10.5, weight=600, pad=6, h=18, anchor="start"):
    w = text_w(s, size, weight) + 2 * pad
    if anchor == "middle":
        x -= w / 2
    rect(x, y, w, h, fill=bg, stroke="none", rx=h / 2)
    text(x + w / 2, y + h / 2 + size * 0.36, s, size, weight, fg, "middle")
    return w


def wrap(s, size, weight, maxw):
    words = s.split()
    lines, cur = [], ""
    for w in words:
        trial = w if not cur else cur + " " + w
        if text_w(trial, size, weight) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def icon(name, x, y, size, color=None, stroke_w=None):
    path = ICONS / name
    root = etree.parse(str(path)).getroot()
    _uid[0] += 1
    pre = f"i{_uid[0]}_"
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        if "id" in el.attrib:
            el.attrib["id"] = pre + el.attrib["id"]
        for k, v in list(el.attrib.items()):
            if "url(#" in v:
                el.attrib[k] = v.replace("url(#", "url(#" + pre)
            if k.endswith("href") and v.startswith("#"):
                el.attrib[k] = "#" + pre + v[1:]
    for k in ("class", "role", "width", "height", "x", "y"):
        root.attrib.pop(k, None)
    for t in root.findall("{http://www.w3.org/2000/svg}title"):
        root.remove(t)
    if "lucide" in str(path):
        root.attrib["stroke"] = color or NAVY
        root.attrib["stroke-width"] = str(stroke_w or 1.75)
        root.attrib["fill"] = "none"
    elif "simple" in str(path):
        root.attrib["fill"] = color or SI_HEX.get(path.stem, NAVY)
    root.attrib.update({"x": f"{x:.1f}", "y": f"{y:.1f}", "width": f"{size}", "height": f"{size}"})
    s = etree.tostring(root, encoding="unicode")
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = s.replace(' xmlns="http://www.w3.org/2000/svg"', "", 1) if out else s
    out.append(s)


def icon_disc(name, cx, cy, r=17, fg=NAVY, bg="#EAF0F6", size=None, simple=False):
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{bg}"/>')
    s = size or r * 1.15
    if simple or str(name).startswith("simple/"):
        icon(name, cx - s / 2, cy - s / 2, s)
    else:
        icon(name, cx - s / 2, cy - s / 2, s, fg)


def poly(points, color, sw=2, dash=None, head=True, r=8):
    d = f"M{points[0][0]:.1f},{points[0][1]:.1f}"
    for i in range(1, len(points) - 1):
        (x0, y0), (x1, y1), (x2, y2) = points[i - 1], points[i], points[i + 1]

        def toward(ax, ay, bx, by, dist):
            L = max(((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5, 1e-6)
            dist = min(dist, L / 2)
            return ax + (bx - ax) * dist / L, ay + (by - ay) * dist / L

        p1 = toward(x1, y1, x0, y0, r)
        p2 = toward(x1, y1, x2, y2, r)
        d += f" L{p1[0]:.1f},{p1[1]:.1f} Q{x1:.1f},{y1:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    (xa, ya), (xb, yb) = points[-2], points[-1]
    L = max(((xb - xa) ** 2 + (yb - ya) ** 2) ** 0.5, 1e-6)
    hl = 9 + sw
    ex, ey = (xb - (xb - xa) * hl * 0.6 / L, yb - (yb - ya) * hl * 0.6 / L) if head else (xb, yb)
    d += f" L{ex:.1f},{ey:.1f}"
    da = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" '
        f'stroke-linecap="round" stroke-linejoin="round"{da}/>'
    )
    if head:
        arrowhead(points[-2], points[-1], color, sw)


def arrowhead(p0, p1, color, sw):
    (xa, ya), (xb, yb) = p0, p1
    L = max(((xb - xa) ** 2 + (yb - ya) ** 2) ** 0.5, 1e-6)
    ux, uy = (xb - xa) / L, (yb - ya) / L
    hl, hw = 9 + sw, 4.5 + sw * 0.75
    bx, by = xb - ux * hl, yb - uy * hl
    pts = [(xb, yb), (bx - uy * hw, by + ux * hw), (bx + ux * 2.2, by + uy * 2.2), (bx + uy * hw, by - ux * hw)]
    out.append('<path d="M' + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + f' Z" fill="{color}"/>')


def zone(x, y, w, h, title, sub=None, color=GREY, fill=ZONE, dash="6 5", tab_icon=None, title_color=None):
    rect(x, y, w, h, fill=fill, stroke=color, sw=1.3, rx=10, dash=dash)
    tx = x + 16
    if tab_icon:
        icon(tab_icon, tx, y + 11, 16, title_color or color)
        tx += 22
    text(tx, y + 24, title.upper(), 11.5, 700, title_color or color, ls=0.8)
    if sub:
        tw = text_w(title.upper(), 11.5, 700) + 0.8 * len(title)
        text(tx + tw + 10, y + 24, sub, 11.5, 400, GREY, maxw=w - (tx - x) - tw - 20)


def card(x, y, w, h, ic, title, sub, opt=False, disc_bg="#EAF0F6", disc_fg=NAVY, ic_simple=False, stroke=None):
    st = stroke or ("#AEBBC8" if opt else "#DCE3EA")
    rect(x, y, w, h, fill="#FBFCFD" if opt else "#FFFFFF", stroke=st, rx=8, dash="4 3" if opt else None, sw=1.2)
    icon_disc(ic, x + 28, y + 28, 16, fg=disc_fg, bg=disc_bg, simple=ic_simple)
    text(x + 52, y + 24, title, 13, 650, GREY if opt else NAVY, maxw=w - 66)
    if sub:
        text(x + 52, y + 42, sub, 11, 400, GREY, maxw=w - 66)
    return x, y, w, h


def build():
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="{FONT}">'
    )
    out.append(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')

    # ---------------------------------------------------------------- header
    text(48, 50, "Data Governance Framework Automation", 30, 650, NAVY)
    text(
        48,
        78,
        "Reference architecture for a fictional multi-domain European group  ·  "
        "Open-source default  ·  Optional buy adapters  ·  Labels export to the AI Governance Platform",
        15,
        400,
        GREY,
        maxw=1700,
    )
    lab = "Local lab on Docker Compose  ·  oss profile  ·  no cloud account"
    tw = text_w(lab, 12.5, 500)
    bx = W - 40
    rect(bx - tw - 56, 38, tw + 56, 34, fill="#F1F6FB", stroke="#D6E2EE", rx=17)
    icon("simple/docker.svg", bx - tw - 44, 45, 21)
    text(bx - 16, 60, lab, 12.5, 500, NAVY2, "end")
    out.append(f'<line x1="48" y1="102" x2="{W-40}" y2="102" stroke="#E4E9EE" stroke-width="1"/>')

    # layered reading key (pyramid inspiration, drawn as a left-to-right stack)
    layers = [
        ("1  Sources", "#EAF0F6", NAVY2),
        ("2  Contracts & quality", TEAL_L, TEAL),
        ("3  Governance core", "#E3EEF8", NAVY),
        ("4  Consumers & AI", GREEN_L, GREEN),
    ]
    lx = 48
    for i, (lab_, bg, fg) in enumerate(layers):
        ww = text_w(lab_, 11, 600) + 20
        rect(lx, 112, ww, 22, fill=bg, stroke="none", rx=4)
        text(lx + 10, 128, lab_, 11, 600, fg)
        if i < len(layers) - 1:
            text(lx + ww + 8, 128, "→", 12, 500, GREY2)
            lx += ww + 24
        else:
            lx += ww + 16
    text(lx + 8, 128, "Read left to right, then follow the request trace below.", 11.5, 400, GREY)

    # ================================================================ ZONES
    SZ = (40, 146, 350, 722)
    zone(*SZ, "1  ·  Sources", "synthetic only  ·  four domains", color=NAVY2, tab_icon="lucide/database.svg")

    CZ = (406, 146, 1124, 722)
    zone(
        *CZ,
        "2–3  ·  Governance core",
        "our operating model around the critical data elements",
        color=TEAL,
        fill="#F7FBFB",
        tab_icon="lucide/shield-check.svg",
    )

    KZ = (1546, 146, 614, 722)
    zone(
        *KZ,
        "4  ·  Consumers",
        "analytics, evidence, AI labels",
        color=GREEN,
        fill="#F6FBF8",
        tab_icon="lucide/layout-dashboard.svg",
        title_color=GREEN,
    )

    # -------------------- sources cards
    domains = [
        ("lucide/users.svg", "Customer domain", "CRM extract  ·  party, contact, account"),
        ("lucide/package.svg", "Product domain", "Product / material master  ·  hierarchy"),
        ("lucide/landmark.svg", "Finance domain", "Vendor, invoice, cost centre  ·  synthetic"),
        ("lucide/id-card.svg", "HR domain", "Employee master  ·  synthetic PII only"),
    ]
    sx, sw = 58, 314
    sy = 190
    for ic, t1, t2 in domains:
        card(sx, sy, sw, 92, ic, t1, t2, disc_bg="#EAF0F6", disc_fg=NAVY2)
        text(sx + 52, sy + 62, "Critical data elements declared in contracts", 10.5, 400, GREY2, maxw=sw - 66)
        sy += 104
    # optional SAP
    card(
        sx,
        sy,
        sw,
        100,
        "simple/sap.svg",
        "Optional SAP connector",
        "Documented only  ·  not implemented",
        opt=True,
        ic_simple=True,
    )
    text(sx + 52, sy + 62, "S/4-style extract, if a client already runs SAP.", 10.5, 400, GREY, maxw=sw - 66)
    text(sx + 52, sy + 78, "SAP MDG remains a buy option, not a lab clone.", 10.5, 400, GREY, maxw=sw - 66)
    text(sx + 16, 846, "No real customer, employee or employer data.", 11, 400, GREY2, maxw=sw)

    # -------------------- buy adapters (compact chip row — keeps the ring clear)
    text(428, 180, "OPTIONAL BUY ADAPTERS", 10, 700, GREY2, ls=0.8)
    text(428, 196, "Same metadata contract  ·  feature-flagged  ·  not required for make demo  ·  dashed = not a lab skill claim", 11, 400, GREY)
    buys = [
        ("simple/microsoft.svg", "Microsoft Purview  ·  optional adapter, limits TODO", True),
        ("lucide/library.svg", "Collibra  ·  buy, documented mapping only", False),
        ("simple/sap.svg", "SAP MDG  ·  buy, not implemented", True),
    ]
    bx = 428
    by = 208
    for ic, lab, simple in buys:
        tw = text_w(lab, 11, 600)
        ww = tw + 40
        rect(bx, by, ww, 28, fill="#FBFCFD", stroke="#AEBBC8", sw=1.1, rx=14, dash="4 3")
        if simple:
            icon(ic, bx + 8, by + 5, 18)
        else:
            icon(ic, bx + 8, by + 5, 18, GREY)
        text(bx + 30, by + 19, lab, 11, 600, GREY)
        bx += ww + 12

    # -------------------- the harness ring (angles offset so cards miss the chip row and humans)
    cx, cy, R, r_in = 968, 530, 178, 86
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{R + 44}" fill="#F4FAFA" stroke="{TEAL_LINE}" stroke-width="1.2"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{R + 44}" fill="none" stroke="{TEAL}" stroke-width="1.6" stroke-dasharray="2 8" opacity="0.55"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{TEAL}" stroke-width="2.2"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r_in}" fill="#FFFFFF" stroke="{TEAL_LINE}" stroke-width="1.4"/>')
    text(cx, cy - 22, "Critical data", 13, 700, NAVY, "middle")
    text(cx, cy - 6, "elements", 13, 700, NAVY, "middle")
    text(cx, cy + 14, "Customer · Product", 10.5, 400, GREY, "middle")
    text(cx, cy + 28, "Finance · HR", 10.5, 400, GREY, "middle")
    text(cx, cy + 48, "the harness", 10, 600, TEAL, "middle", ls=0.6)

    nodes = [
        (30, "lucide/library.svg", "Catalog & glossary", "OpenMetadata default"),
        (90, "lucide/list-checks.svg", "Quality & KPIs", "Great Expectations · dbt"),
        (150, "lucide/file-cog.svg", "Data contracts", "versioned YAML / ODCS"),
        (210, "lucide/user-check.svg", "Ownership / RACI", "owner · steward · RACI"),
        (270, "lucide/tags.svg", "Classification & RoPA", "PII · confidential · fit_for_ai"),
        (330, "lucide/git-branch.svg", "Lineage", "source → mart → KPI"),
    ]
    for ang, ic, t1, t2 in nodes:
        rad = math.radians(ang - 90)
        nx = cx + R * math.cos(rad)
        ny = cy + R * math.sin(rad)
        out.append(f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="7" fill="{TEAL}" stroke="#FFFFFF" stroke-width="2"/>')
        outward = 74
        ox = cx + (R + outward) * math.cos(rad)
        oy = cy + (R + outward) * math.sin(rad)
        cw, ch = 208, 56
        if 0 <= ang < 60:          # top-right
            rx, ry = ox - 24, oy - ch - 4
        elif 60 <= ang < 120:      # right
            rx, ry = ox + 8, oy - ch / 2
        elif 120 <= ang < 180:     # bottom-right, sit to the side not under the ring
            rx, ry = ox + 8, oy - ch / 2
        elif 180 <= ang < 240:     # bottom-left, sit to the side
            rx, ry = ox - cw - 8, oy - ch / 2
        elif 240 <= ang < 300:     # left
            rx, ry = ox - cw - 8, oy - ch / 2
        else:                      # top-left
            rx, ry = ox - cw + 24, oy - ch - 4
        rect(rx, ry, cw, ch, fill="#FFFFFF", stroke=TEAL_LINE, sw=1.2, rx=8)
        icon(ic, rx + 10, ry + 15, 24, TEAL)
        text(rx + 40, ry + 23, t1, 12, 650, NAVY, maxw=cw - 50)
        text(rx + 40, ry + 41, t2, 10.5, 400, GREY, maxw=cw - 50)

    text(cx, 800, "Operating model — our code   ·   DAMA-DMBOK mapped   ·   feature flag oss | hybrid", 11.5, 500, TEAL, "middle")

    humans = [
        ("lucide/briefcase.svg", "Domain Data Owner"),
        ("lucide/user-check.svg", "Data Steward"),
        ("lucide/scale.svg", "DPO / IT / security"),
    ]
    hw = 200
    hx0 = cx - (3 * hw + 2 * 16) / 2
    for i, (ic, lab_) in enumerate(humans):
        x = hx0 + i * (hw + 16)
        rect(x, 814, hw, 42, fill=AMBER_L, stroke="#E8C989", sw=1.2, rx=8)
        icon(ic, x + 12, 824, 22, AMBER)
        text(x + 40, 841, lab_, 12, 600, AMBER)

    # -------------------- consumers
    kx, kw = 1566, 574
    ky = 190
    consumers = [
        (False, "lucide/layout-dashboard.svg", "Quality KPI scorecard", "Measured (run demo-2026-11-15T111652Z): completeness 0.762, uniqueness 0.875, consistency 0.714, currentness 0.40, key match 0.857.", "#EAF0F6", NAVY2),
        (False, "lucide/boxes.svg", "Domain data products  ·  dbt", "dbt marts for the four domains, served under the data contract.", "#EAF0F6", NAVY2),
        (False, "lucide/file-text.svg", "Evidence pack  ·  make report", "PDF case-study pack. Policies, RACI, RoPA, issue log. No invented numbers.", "#EAF0F6", NAVY2),
        (True, "lucide/tags.svg", "Label export", "{asset, field, classification, owner, steward, fit_for_ai, policy_version}", GREEN_L, GREEN),
        (True, "lucide/shield-check.svg", "AI Compliance Automation", "Existing  ·  Semantic Guard + OPA consume labels only.", GREEN_L, GREEN),
        (True, "lucide/bot.svg", "Agent Access Governance Gateway", "Existing  ·  allow / ask / deny on unclassified or non-approved data.", GREEN_L, GREEN),
    ]
    for existing, ic, t1, t2, bg, fg in consumers:
        simple = ic.startswith("simple/")
        h = 86 if existing else 80
        st = GREEN_LINE if existing else "#DCE3EA"
        rect(kx, ky, kw, h, fill="#FFFFFF", stroke=st, sw=1.3 if existing else 1.2, rx=8)
        if existing:
            rect(kx, ky, 6, h, fill=GREEN, stroke="none", rx=3)
        icon_disc(ic, kx + 32, ky + 28, 16, fg=fg or NAVY2, bg=bg or "#EAF0F6", simple=simple)
        text(kx + 56, ky + 24, t1, 13, 650, GREEN if existing else NAVY, maxw=kw - 70)
        text(kx + 56, ky + 44, t2, 11, 400, GREY, maxw=kw - 70)
        ky += h + 12
    text(kx, 846, "Green = already-built AI Governance Platform components. This repo only publishes labels.", 10.5, 400, GREY, maxw=kw)

    # source → core arrows
    for i in range(4):
        y = 190 + 46 + i * 104
        poly([(58 + 314, y), (406, y)], LINE, sw=1.4, head=True)
    label_y = 190 + 46 + 1.5 * 104
    text(400, label_y - 10, "extracts under contract", 10.5, 500, GREY, "end", halo=True)

    # core to consumers — aim at mid of catalogued vs labels, keep clear of ring cards
    poly([(406 + 1124, 400), (1546, 400)], TEAL, sw=1.8, head=True)
    text(1496, 388, "catalogued, owned, classified", 10.5, 500, TEAL, "end", halo=True)
    poly([(406 + 1124, 720), (1546, 720)], GREEN, sw=1.8, head=True)
    text(1518, 708, "label pack", 10.5, 500, GREEN, "end", halo=True)

    # ================================================================ TRACE
    FX, FY, FW, FH = 40, 884, 1488, 448
    rect(FX, FY, FW, FH, fill="#FBFCFD", stroke="#D5DDE5", sw=1.3, rx=10)
    chip(FX + 20, FY + 16, "Follow a request", TEAL, TEAL_L, size=11.5, weight=700, pad=10, h=24)
    text(FX + 168, FY + 34, "Decision trace  ·  taken path in teal  ·  blocked or not-approved path in grey", 13, 400, GREY)

    def node_box(x, y, w, h, title, lines, color=NAVY, fill="#FFFFFF", ic=None, ic_fg=None):
        rect(x, y, w, h, fill=fill, stroke=color, sw=1.4, rx=8)
        if ic:
            icon(ic, x + 10, y + 10, 18, ic_fg or color)
            text(x + 34, y + 24, title, 12.5, 650, color, maxw=w - 44)
        else:
            text(x + 12, y + 24, title, 12.5, 650, color, maxw=w - 20)
        for i, ln in enumerate(lines):
            text(x + 12, y + 44 + i * 16, ln, 11, 400, GREY, maxw=w - 22)

    nw, nh = 200, 86
    y_main = FY + 58
    xs = [FX + 28, FX + 268, FX + 508]
    node_box(xs[0], y_main, nw, nh, "Business request", ["“Export these customers", "for a local campaign.”"], NAVY2, ic="lucide/briefcase.svg")
    node_box(xs[1], y_main, nw, nh, "Catalog & contract", ["Owner, definition and", "classification looked up."], TEAL, ic="lucide/library.svg", ic_fg=TEAL)
    node_box(xs[2], y_main, nw, nh, "Quality gate", ["Great Expectations and", "dbt / contract tests."], TEAL, ic="lucide/list-checks.svg", ic_fg=TEAL)
    for a, b in ((0, 1), (1, 2)):
        poly([(xs[a] + nw, y_main + nh / 2), (xs[b], y_main + nh / 2)], TEAL, sw=2.2)

    x_ok = FX + 748
    node_box(x_ok, y_main, nw, nh, "Approved data product", ["Pass  ·  contract held.", "Ready for the KPI mart."], GREEN, GREEN_L, ic="lucide/circle-check.svg", ic_fg=GREEN)
    poly([(xs[2] + nw, y_main + nh / 2), (x_ok, y_main + nh / 2)], TEAL, sw=2.2)
    text((xs[2] + nw + x_ok) / 2, y_main + nh / 2 - 10, "pass", 10.5, 600, TEAL, "middle", halo=True)
    x_cons = FX + 988
    node_box(x_cons, y_main, 220, nh, "BI / evidence consumer", ["KPI board or report.", "Lineage intact."], GREEN, GREEN_L, ic="lucide/layout-dashboard.svg", ic_fg=GREEN)
    poly([(x_ok + nw, y_main + nh / 2), (x_cons, y_main + nh / 2)], GREEN, sw=2.2)

    # Fail branch stays under the quality gate, clear of the AI branch
    y_fail = FY + 188
    x_fail = xs[2]
    node_box(x_fail, y_fail, nw, nh, "Steward issue", ["Fail  ·  owner/steward", "records a decision."], AMBER, AMBER_L, ic="lucide/git-pull-request.svg", ic_fg=AMBER)
    poly([(xs[2] + nw / 2, y_main + nh), (xs[2] + nw / 2, y_fail)], AMBER, sw=2.0)
    text(xs[2] + nw / 2 + 12, y_main + nh + 24, "fail", 10.5, 600, AMBER, halo=True)
    x_fix = x_ok
    node_box(x_fix, y_fail, nw, nh, "Cleanse or rule change", ["Versioned fix, then", "re-run the quality gate."], AMBER, AMBER_L, ic="lucide/workflow.svg", ic_fg=AMBER)
    poly([(x_fail + nw, y_fail + nh / 2), (x_fix, y_fail + nh / 2)], AMBER, sw=2.0)

    # AI branches drop from the approved product, on the right — no crossing of the main path
    y_ai = FY + 328
    node_box(
        x_ok, y_ai, 230, nh,
        "AI path  ·  allowed",
        ["Non-PII KPI aggregate.", "Gateway returns allow."],
        GREEN, GREEN_L, ic="lucide/bot.svg", ic_fg=GREEN,
    )
    node_box(
        x_ok + 250, y_ai, 280, nh,
        "AI path  ·  deny / ask",
        ["pii.contact or not_fit_for_ai.", "Grey = branch not taken."],
        GREY, "#F3F4F6", ic="lucide/circle-x.svg", ic_fg=GREY,
    )
    poly([(x_ok + nw / 2, y_main + nh), (x_ok + nw / 2, y_ai)], GREEN, sw=2.0)
    # nudge the deny connector from mid of approved box slightly right, then down, without crossing fail boxes
    mid_y = y_fail + nh + 22
    poly(
        [(x_ok + nw / 2, y_main + nh), (x_ok + nw / 2, mid_y), (x_ok + 250 + 140, mid_y), (x_ok + 250 + 140, y_ai)],
        GREY2, sw=1.6, dash="5 4",
    )
    text(x_ok + nw / 2 + 12, (y_fail + nh + y_ai) / 2 + 4, "fit_for_ai", 10.5, 600, GREEN, halo=True)
    text(x_ok + 250 + 8, mid_y - 8, "not_fit_for_ai", 10.5, 600, GREY, halo=True)

    text(
        FX + 28,
        FY + FH - 18,
        "Fictional Tarsfeld Group  ·  Northwind Advisory case  ·  the same path must also run under the hybrid profile once Purview limits are checked.",
        11.5, 400, GREY, maxw=FW - 50,
    )

    # ================================================================ LEGEND
    LX, LY, LW, LH = 1546, 884, 614, 448
    rect(LX, LY, LW, LH, fill="#FFFFFF", stroke="#D5DDE5", sw=1.3, rx=10)
    text(LX + 20, LY + 30, "LEGEND", 11.5, 700, GREY, ls=0.8)

    def swatch(x, y, fill, stroke, dash, label):
        rect(x, y, 26, 16, fill=fill, stroke=stroke, sw=1.3, rx=3, dash=dash)
        text(x + 36, y + 13, label, 12, 400, INK)

    def leg_line(x, y, color, sw, dash, label):
        poly([(x, y), (x + 44, y)], color, sw=sw, dash=dash)
        text(x + 56, y + 4, label, 12, 400, INK)

    swatch(LX + 20, LY + 50, "#F7FBFB", TEAL, "6 5", "Governance core  ·  our operating model")
    swatch(LX + 20, LY + 76, "#F6FBF8", GREEN, "6 5", "Existing AI Governance Platform")
    swatch(LX + 20, LY + 102, AMBER_L, "#E8C989", None, "Human role in the loop")
    swatch(LX + 20, LY + 128, "#FBFCFD", "#AEBBC8", "4 3", "Optional buy / not implemented")
    swatch(LX + 20, LY + 154, "#F3F4F6", GREY, None, "Trace branch not taken (deny / ask)")

    leg_line(LX + 20, LY + 196, LINE, 1.6, None, "Synthetic extracts under contract")
    leg_line(LX + 20, LY + 222, TEAL, 2.2, None, "Taken path through the gate")
    leg_line(LX + 20, LY + 248, GREEN, 2.0, None, "Approved product or AI allow")
    leg_line(LX + 20, LY + 274, AMBER, 2.0, None, "Failed rule  →  steward issue")
    leg_line(LX + 20, LY + 300, GREY2, 1.6, "5 4", "Blocked or not-approved AI path")

    text(LX + 20, LY + 340, "Icons", 11.5, 700, GREY, ls=0.8)
    # icon row
    icrow = [
        ("simple/python.svg", "Python"),
        ("simple/docker.svg", "Docker"),
        ("simple/sap.svg", "SAP (buy)"),
        ("simple/microsoft.svg", "Microsoft"),
    ]
    ix = LX + 20
    for ic, lab_ in icrow:
        icon(ic, ix, LY + 354, 20)
        text(ix + 24, LY + 370, lab_, 11, 400, INK)
        ix += 24 + text_w(lab_, 11, 400) + 16
    text(ix + 4, LY + 370, "dbt is named in type on the consumer cards.", 11, 400, GREY)
    text(
        LX + 20,
        LY + 410,
        "Lucide pictograms stand in for OpenMetadata, Great Expectations,",
        11,
        400,
        GREY,
        maxw=LW - 40,
    )
    text(
        LX + 20,
        LY + 426,
        "Collibra and Purview — no unofficial vendor marks.",
        11,
        400,
        GREY,
        maxw=LW - 40,
    )

    # ================================================================ FOOTER
    out.append(f'<line x1="48" y1="1352" x2="{W-40}" y2="1352" stroke="#E4E9EE"/>')
    text(48, 1378, "Mir Mansoor Ahmed  ·  Portfolio Lab  ·  fictional client: Tarsfeld Group GmbH  ·  consultancy in examples: Northwind Advisory", 13, 500, NAVY2)
    text(
        48,
        1400,
        "This is a lab design, not a production product, not legal advice, and not a claim that any real firm is compliant. Scorecard metrics are measured on the committed run demo-2026-11-15T111652Z.",
        12,
        400,
        GREY,
        maxw=1700,
    )
    text(W - 40, 1378, "Diagram v2  ·  15 November 2026  ·  Europe/Berlin", 12, 400, GREY2, "end")
    text(W - 40, 1400, "architecture.py  →  architecture.svg / .png", 12, 400, GREY2, "end")
    out.append("</svg>")


def main():
    build()
    svg = "\n".join(out)
    (HERE / "architecture.svg").write_text(svg, encoding="utf-8")
    for w_ in warnings:
        print("WARN", w_, file=sys.stderr)
    html = HERE / ".render.html"
    html.write_text(
        "<!doctype html><html><head><style>html,body{margin:0;padding:0;background:#fff}"
        "svg{display:block}</style></head><body>" + svg + "</body></html>",
        encoding="utf-8",
    )
    chrome = "google-chrome" if Path("/usr/bin/google-chrome").exists() else "google-chrome-stable"
    subprocess.run(
        [
            chrome,
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=2",
            f"--window-size={W},{H}",
            f"--screenshot={HERE / 'architecture.png'}",
            html.as_uri(),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    html.unlink()
    print("wrote", HERE / "architecture.svg", HERE / "architecture.png")


if __name__ == "__main__":
    main()
