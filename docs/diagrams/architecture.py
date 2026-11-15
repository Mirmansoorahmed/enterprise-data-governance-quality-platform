#!/usr/bin/env python3
"""Enterprise Data Governance & Quality Platform — architecture v3 (simple).

One left-to-right flow in four lanes. At most ~15 boxes.
Also writes architecture-explained.png: the same figure plus a numbered
legend panel below (what each box does, and which rule source drives it).
The detailed v2 figure is kept as architecture-v2-detailed.{py,svg,png}.

    python3 architecture.py          # writes architecture.svg/.png and architecture-explained.png
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from lxml import etree
from PIL import ImageFont

HERE = Path(__file__).resolve().parent
ICONS = HERE / "icons"
W, H = 1920, 960
FONT_FILE = "/usr/share/fonts/truetype/sand-box/google/Inter/Inter-VariableFont_opsz,wght.ttf"

NAVY = "#0F2A47"
NAVY2 = "#1F3A5F"
INK = "#1B2B3C"
GREY = "#5B6B7C"
GREY2 = "#8A99A8"
LINE = "#D0D7DE"
CARD = "#FFFFFF"
TEAL = "#0B8A8A"
TEAL_L = "#E7F4F3"
TEAL_LINE = "#9FCFCB"
GREEN = "#047857"
GREEN_L = "#E7F6EE"
GREEN_LINE = "#86D0B0"
AMBER = "#A86A12"
AMBER_L = "#FBF1E1"
FONT = "Inter, 'Segoe UI', Helvetica, Arial, sans-serif"

SI_HEX = {
    "python": "#3776AB",
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


def text(x, y, s, size=14, weight=400, fill=INK, anchor="start", maxw=None, ls=0):
    if maxw is not None:
        w = text_w(s, size, weight)
        if w > maxw + 0.5:
            warnings.append(f"text too wide ({w:.0f}>{maxw:.0f}): {s!r}")
    lsp = f' letter-spacing="{ls}"' if ls else ""
    out.append(
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}"{lsp}>{esc(s)}</text>'
    )


def rect(x, y, w, h, fill=CARD, stroke=LINE, sw=1, rx=10, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{sw}"{d}/>'
    )


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


def icon_disc(name, cx, cy, r=18, fg=NAVY, bg="#EAF0F6", simple=False):
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{bg}"/>')
    s = r * 1.15
    if simple or str(name).startswith("simple/"):
        icon(name, cx - s / 2, cy - s / 2, s)
    else:
        icon(name, cx - s / 2, cy - s / 2, s, fg)


def arrow_right(x1, y, x2, color=TEAL, sw=2.6):
    hl = 11 + sw
    ex = x2 - hl * 0.55
    out.append(
        f'<path d="M{x1:.1f},{y:.1f} L{ex:.1f},{y:.1f}" fill="none" stroke="{color}" '
        f'stroke-width="{sw}" stroke-linecap="round"/>'
    )
    hw = 5.2 + sw * 0.7
    bx = x2 - hl
    pts = [(x2, y), (bx, y - hw), (bx + 2.2, y), (bx, y + hw)]
    out.append('<path d="M' + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + f' Z" fill="{color}"/>')


def arrow_down(x, y1, y2, color=TEAL, sw=2.2):
    hl = 10 + sw
    ey = y2 - hl * 0.55
    out.append(
        f'<path d="M{x:.1f},{y1:.1f} L{x:.1f},{ey:.1f}" fill="none" stroke="{color}" '
        f'stroke-width="{sw}" stroke-linecap="round"/>'
    )
    hw = 5 + sw * 0.7
    by = y2 - hl
    pts = [(x, y2), (x - hw, by), (x, by + 2.2), (x + hw, by)]
    out.append('<path d="M' + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + f' Z" fill="{color}"/>')


def source_tag(x, y, label, fill="#F3F6F8", stroke="#C5D0DA", fg=GREY):
    pad = 8
    tw = text_w(label, 10, 600)
    rect(x, y, tw + pad * 2, 18, fill=fill, stroke=stroke, sw=1, rx=9)
    text(x + pad + tw / 2, y + 13.2, label, 10, 600, fg, "middle")
    return tw + pad * 2


def badge(cx, cy, n):
    """Small numbered marker used only on the explained figure."""
    out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="10" fill="{NAVY}"/>')
    text(cx, cy + 4, str(n), 11, 700, "#FFFFFF", "middle")


def lane(x, y, w, h, title, color, fill):
    rect(x, y, w, h, fill=fill, stroke=color, sw=1.4, rx=14, dash="7 6")
    text(x + 22, y + 34, title.upper(), 13, 700, color, ls=1.0)



def build(explained: bool = False):
    H = 1560 if explained else 960
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="{FONT}">'
    )
    out.append(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')

    def mark(n, bx, by, bw):
        if explained:
            badge(bx + bw - 16, by + 16, n)

    # ----- header
    text(56, 50, "Enterprise Data Governance & Quality Platform", 32, 650, NAVY)
    text(
        56,
        82,
        "Four lanes, left to right  ·  Open-source default  ·  Labels export to the AI Governance Platform",
        16,
        400,
        GREY,
        maxw=1320,
    )
    lab = "oss profile  ·  Docker Compose"
    tw = text_w(lab, 13, 500)
    bx = W - 56
    rect(bx - tw - 52, 34, tw + 52, 32, fill="#F1F6FB", stroke="#D6E2EE", rx=16)
    icon("simple/docker.svg", bx - tw - 40, 40, 20)
    text(bx - 16, 56, lab, 13, 500, NAVY2, "end")
    out.append(f'<line x1="56" y1="104" x2="{W-56}" y2="104" stroke="#E6EBF0" stroke-width="1"/>')

    # ----- four lanes
    LY, LH = 126, 596
    L1 = (56, LY, 300, LH)
    L2 = (400, LY, 300, LH)
    L3 = (744, LY, 620, LH)
    L4 = (1408, LY, 456, LH)

    lane(*L1, "1  ·  Data sources", NAVY2, "#F6F8FA")
    lane(*L2, "2  ·  Contracts & quality gate", TEAL, "#F5FBFA")
    lane(*L3, "3  ·  Governance core", TEAL, "#F5FBFA")
    lane(*L4, "4  ·  Consumers", GREEN, "#F5FAF7")

    mid = LY + 40 + (LH - 48) / 2
    arrow_right(L1[0] + L1[2] + 5, mid, L2[0] - 5, TEAL, 2.6)
    arrow_right(L2[0] + L2[2] + 5, mid, L3[0] - 5, TEAL, 2.6)
    arrow_right(L3[0] + L3[2] + 5, mid, L4[0] - 5, GREEN, 2.6)

    # ===== 1. Sources (1 box) =====
    x, y, w = L1[0] + 18, LY + 56, L1[2] - 36
    rect(x, y, w, 516, fill=CARD, stroke="#C9D3DD", sw=1.3, rx=12)
    mark(1, x, y, w)
    icon_disc("lucide/database.svg", x + 30, y + 34, 20, fg=NAVY2, bg="#EAF0F6")
    text(x + 58, y + 28, "Four domains", 17, 650, NAVY)
    text(x + 58, y + 52, "Synthetic data only", 13, 400, GREY)
    out.append(f'<line x1="{x+18}" y1="{y+76}" x2="{x+w-18}" y2="{y+76}" stroke="#E6EBF0"/>')
    domains = [
        ("lucide/users.svg", "Customer", "CRM  ·  party and contacts"),
        ("lucide/package.svg", "Product", "Product and material master"),
        ("lucide/landmark.svg", "Finance", "Vendor, invoice, cost centre"),
        ("lucide/id-card.svg", "HR", "Employee master  ·  PII"),
    ]
    dy = y + 104
    for ic, t1, t2 in domains:
        icon(ic, x + 22, dy, 26, NAVY2)
        text(x + 58, dy + 10, t1, 16, 650, NAVY, maxw=w - 80)
        text(x + 58, dy + 34, t2, 13, 400, GREY, maxw=w - 80)
        dy += 88
    text(x + 20, y + 492, "No real customer or employee data.", 13, 400, GREY2, maxw=w - 36)

    # ===== 2. Contracts & quality (2 boxes) =====
    x, w = L2[0] + 18, L2[2] - 36
    y1 = LY + 56
    h_box = 220
    rect(x, y1, w, h_box, fill=CARD, stroke=TEAL_LINE, sw=1.4, rx=12)
    mark(2, x, y1, w)
    icon_disc("lucide/file-cog.svg", x + 30, y1 + 34, 20, fg=TEAL, bg=TEAL_L)
    text(x + 58, y1 + 28, "Data contracts", 17, 650, NAVY)
    text(x + 58, y1 + 52, "Versioned YAML / ODCS", 13, 400, GREY)
    for i, line in enumerate((
        "Declares the critical data",
        "elements in each domain, and",
        "the rule that must hold before",
        "data can move on.",
    )):
        text(x + 22, y1 + 92 + i * 26, line, 14, 400, INK, maxw=w - 40)

    arrow_down(x + w / 2, y1 + h_box + 4, y1 + h_box + 24, TEAL, 2.2)

    y2 = y1 + h_box + 28
    rect(x, y2, w, h_box, fill=CARD, stroke=TEAL_LINE, sw=1.4, rx=12)
    mark(3, x, y2, w)
    icon_disc("lucide/list-checks.svg", x + 30, y2 + 34, 20, fg=TEAL, bg=TEAL_L)
    text(x + 58, y2 + 28, "Quality gate", 17, 650, NAVY)
    text(x + 58, y2 + 52, "Great Expectations  ·  dbt", 13, 400, GREY)
    for i, line in enumerate((
        "Completeness, uniqueness",
        "and consistency. A fail opens",
        "a steward issue — it is never",
        "a silent skip.",
    )):
        text(x + 22, y2 + 88 + i * 24, line, 14, 400, INK, maxw=w - 40)
    source_tag(x + 18, y2 + h_box - 30, "ISO 8000 / ISO/IEC 25012")

    # ===== 3. Governance core (5 boxes) =====
    x, w = L3[0] + 18, L3[2] - 36
    y = LY + 56
    ch, gap = 124, 18
    rect(x, y, w, ch, fill=CARD, stroke=TEAL_LINE, sw=1.4, rx=12)
    mark(4, x, y, w)
    icon_disc("lucide/library.svg", x + 30, y + 36, 20, fg=TEAL, bg=TEAL_L)
    text(x + 60, y + 32, "Catalog & glossary", 17, 650, NAVY)
    text(x + 60, y + 56, "OpenMetadata  ·  default", 13, 400, GREY)
    text(
        x + 22,
        y + 96,
        "Definitions for the critical elements, in English with German aliases.",
        14,
        400,
        INK,
        maxw=w - 44,
    )

    hw = (w - gap) / 2
    hh = 168
    cells = [
        (0, 0, 5, "lucide/git-branch.svg", "Lineage",
         ("Source → mart → KPI,", "so a number can be traced."), None),
        (1, 0, 6, "lucide/tags.svg", "Classification",
         ("PII, confidential, and", "fit_for_ai / not_fit_for_ai."), "GDPR Art. 5/30/32"),
        (0, 1, 7, "lucide/user-check.svg", "Ownership / RACI",
         ("A named Data Owner and a", "Data Steward per element."), None),
        (1, 1, 8, "lucide/file-text.svg", "Policies",
         ("Standards, access, retention,", "and a short RoPA register."), "GDPR Art. 5/30/32"),
    ]
    gy0 = y + ch + gap
    for col, row, num, ic, t1, lines, tag in cells:
        cx = x + col * (hw + gap)
        cy = gy0 + row * (hh + gap)
        rect(cx, cy, hw, hh, fill=CARD, stroke=TEAL_LINE, sw=1.4, rx=12)
        mark(num, cx, cy, hw)
        icon_disc(ic, cx + 28, cy + 32, 18, fg=TEAL, bg=TEAL_L)
        text(cx + 54, cy + 38, t1, 16, 650, NAVY, maxw=hw - 86)
        text(cx + 20, cy + 78, lines[0], 14, 400, INK, maxw=hw - 36)
        text(cx + 20, cy + 102, lines[1], 14, 400, INK, maxw=hw - 36)
        if tag:
            source_tag(cx + 16, cy + hh - 28, tag)

    # ===== 4. Consumers (3 boxes) =====
    x, w = L4[0] + 18, L4[2] - 36
    items = [
        (9, False, "lucide/layout-dashboard.svg", "KPI scorecard",
         ("Completeness, uniqueness,", "consistency. TARGETS until", "a committed run exists."), None),
        (10, False, "lucide/boxes.svg", "Data products",
         ("dbt marts for the four", "domains, served under", "the data contract."), None),
        (11, True, "lucide/shield-check.svg", "AI label export",
         ("Owner, classification and", "fit_for_ai go to the AI platform."),
         "EU AI Act Art. 10"),
    ]
    cy = LY + 56
    hh, gapc = 160, 16
    for num, existing, ic, t1, lines, tag in items:
        st = GREEN_LINE if existing else "#C9D3DD"
        rect(x, cy, w, hh, fill=CARD, stroke=st, sw=1.4, rx=12)
        mark(num, x, cy, w)
        if existing:
            rect(x, cy, 7, hh, fill=GREEN, stroke="none", rx=3)
        bg, fg = (GREEN_L, GREEN) if existing else ("#EAF0F6", NAVY2)
        icon_disc(ic, x + 32, cy + 32, 18, fg=fg, bg=bg)
        text(x + 60, cy + 38, t1, 17, 650, GREEN if existing else NAVY, maxw=w - 90)
        for i, line in enumerate(lines):
            text(x + 20, cy + 76 + i * 22, line, 14, 400, INK, maxw=w - 36)
        if tag:
            source_tag(x + 16, cy + hh - 28, tag)
        cy += hh + gapc

    # ===== bottom strip: humans, buy adapters, tiny trace =====
    BY = 742
    # Human roles — one small strip
    hx, hw, hh = 56, 644, 86
    rect(hx, BY, hw, hh, fill=AMBER_L, stroke="#E8C989", sw=1.3, rx=12)
    mark(12, hx, BY, hw)
    text(hx + 20, BY + 22, "PEOPLE IN THE LOOP", 11, 700, AMBER, ls=0.8)
    roles = [
        ("lucide/briefcase.svg", "Data Owner", None),
        ("lucide/user-check.svg", "Data Steward", "(Datenverantwortlicher)"),
        ("lucide/scale.svg", "DPO", None),
    ]
    rx = hx + 16
    for ic, lab_, sub in roles:
        icon(ic, rx, BY + 40, 22, AMBER)
        text(rx + 28, BY + 52 if sub else BY + 60, lab_, 15, 600, AMBER)
        if sub:
            text(rx + 28, BY + 70, sub, 11, 500, AMBER)
            block = max(text_w(lab_, 15, 600), text_w(sub, 11, 500))
        else:
            block = text_w(lab_, 15, 600)
        rx += 28 + block + 28

    # Buy adapters — one dashed box
    bx0, bw = 744, 620
    rect(bx0, BY, bw, hh, fill="#FBFCFD", stroke="#AEBBC8", sw=1.3, rx=12, dash="6 5")
    mark(13, bx0, BY, bw)
    text(bx0 + 20, BY + 24, "OPTIONAL BUY  ·  NOT BUILT", 11, 700, GREY, ls=0.8)
    buys = [
        ("simple/microsoft.svg", "Microsoft Purview"),
        ("lucide/library.svg", "Collibra"),
        ("simple/sap.svg", "SAP MDG"),
    ]
    rx = bx0 + 16
    for ic, lab_ in buys:
        if ic.startswith("simple/"):
            icon(ic, rx, BY + 42, 22)
        else:
            icon(ic, rx, BY + 42, 22, GREY)
        text(rx + 28, BY + 60, lab_, 15, 600, GREY)
        rx += 28 + text_w(lab_, 15, 600) + 24

    # Tiny trace inset — three outcomes
    tx, tw_box = 1408, 456
    rect(tx, BY, tw_box, hh, fill="#FBFCFD", stroke="#D0D7DE", sw=1.3, rx=12)
    mark(14, tx, BY, tw_box)
    text(tx + 18, BY + 24, "A REQUEST CAN END IN", 11, 700, GREY, ls=0.8)
    outcomes = [
        (GREEN, GREEN_L, "Pass"),
        (AMBER, AMBER_L, "Steward fix"),
        (GREY, "#F3F4F6", "Deny / ask"),
    ]
    ox = tx + 16
    for fg, bg, lab_ in outcomes:
        ww = text_w(lab_, 14, 650) + 20
        rect(ox, BY + 40, ww, 30, fill=bg, stroke=fg, sw=1.2, rx=15)
        text(ox + ww / 2, BY + 61, lab_, 14, 650, fg, "middle")
        ox += ww + 10

    # ===== minimal legend + one footer line =====
    out.append(f'<line x1="56" y1="848" x2="{W-56}" y2="848" stroke="#E6EBF0" stroke-width="1"/>')

    def swatch(x, y, fill, stroke, dash, label):
        rect(x, y, 22, 14, fill=fill, stroke=stroke, sw=1.3, rx=3, dash=dash)
        text(x + 30, y + 12, label, 13, 400, INK)

    lx, ly = 56, 870
    swatch(lx, ly, "#F5FBFA", TEAL, "7 6", "Governance core")
    swatch(lx + 200, ly, "#F5FAF7", GREEN, "7 6", "Existing AI platform")
    swatch(lx + 430, ly, AMBER_L, "#E8C989", None, "Human role")
    swatch(lx + 600, ly, "#FBFCFD", "#AEBBC8", "6 5", "Optional buy")

    text(
        56,
        928,
        "Mir Mansoor Ahmed  ·  Enterprise Data Governance & Quality Platform  ·  Tarsfeld Group (fiction)  ·  14 November 2026  ·  RULES-AND-POLICIES.md",
        13,
        500,
        NAVY2,
        maxw=1550,
    )
    text(W - 56, 928, "v3  ·  architecture.py", 13, 400, GREY2, "end")

    if explained:
        panel_y = 960
        panel_h = 548
        rect(56, panel_y, W - 112, panel_h, fill="#F6F8FA", stroke="#D0D7DE", sw=1.2, rx=14)
        text(80, panel_y + 36, "How to read this figure", 22, 650, NAVY)
        text(
            80,
            panel_y + 62,
            "Each number matches a box above. 1–2 lines say what it does and which rule source drives it. Full catalog: RULES-AND-POLICIES.md.",
            14,
            400,
            GREY,
            maxw=W - 180,
        )
        items_exp = [
            (1, "Data sources",
             "Synthetic Customer, Product, Finance and HR extracts only. Four domains let quality and privacy rules sit side by side."),
            (2, "Data contracts",
             "Versioned YAML/ODCS agreements and the rule that must hold. Source: ISO 8000-110 (conformance to a data specification)."),
            (3, "Quality gate",
             "Automated checks for completeness, uniqueness, consistency and currentness. Sources: ISO 8000 (parts 8, 61, 110) and ISO/IEC 25012. A fail opens a steward issue."),
            (4, "Catalog & glossary",
             "Business definitions and technical metadata for critical elements, in English with German aliases. Source: DAMA-DMBOK Metadata Management."),
            (5, "Lineage",
             "Trace a KPI or an export back to its source so a number can be explained. No single statutory article; it is the evidence path for the other rules."),
            (6, "Classification",
             "Tags such as PII and confidential, required so minimisation and access rules can run. Source: GDPR Art. 5, 30 and 32."),
            (7, "Ownership / RACI",
             "A Data Owner is accountable and a Data Steward (Datenverantwortlicher) is responsible for each critical element. Source: DAMA-DMBOK Data Governance and Stewardship."),
            (8, "Policies",
             "Written standards for access, retention and a short RoPA register. Source: GDPR Art. 5, Art. 30 and Art. 32."),
            (9, "KPI scorecard",
             "Quality dimensions reported as TARGETS until a committed run exists. Process frame: ISO 8000-61; dimensions: ISO/IEC 25012."),
            (10, "Data products",
             "Approved dbt marts for the four domains, served only under the data contract and after the quality gate."),
            (11, "AI label export",
             "Owner, classification and the fit_for_ai label go to the AI Governance Platform. Source: EU AI Act Art. 10 (Data and data governance). Not a conformity assessment."),
            (12, "People in the loop",
             "Data Owner, Data Steward (Datenverantwortlicher) and DPO stay in the operating model. See RULES-AND-POLICIES.md §7 on why those titles are used."),
            (13, "Optional buy",
             "Microsoft Purview, Collibra and SAP MDG are adapters or buy recommendations, not built in this lab."),
            (14, "Request outcomes",
             "A request can end in pass, a steward fix, or deny/ask. Nothing fails silently. Steward-fix is the path for a failed quality or policy check."),
        ]
        col_w = (W - 112 - 48) / 2
        row_h = 58
        origin_y = panel_y + 86
        for i, (n, title, body) in enumerate(items_exp):
            col = i % 2
            row = i // 2
            ix = 80 + col * (col_w + 16)
            iy = origin_y + row * row_h
            badge(ix + 10, iy + 12, n)
            text(ix + 28, iy + 16, title, 14, 650, NAVY, maxw=col_w - 40)
            # wrap body to two lines if needed
            words = body.split()
            lines, cur = [], ""
            for word in words:
                trial = (cur + " " + word).strip()
                if text_w(trial, 12, 400) <= col_w - 40:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    cur = word
            if cur:
                lines.append(cur)
            if len(lines) > 2:
                # squeeze leftover onto line 2
                lines = [lines[0], " ".join(lines[1:])]
                # if still too wide, the text() maxw warning will flag it
            for j, line in enumerate(lines[:2]):
                text(ix + 28, iy + 36 + j * 16, line, 12, 400, INK, maxw=col_w - 40)

        text(
            56,
            1540,
            "Mir Mansoor Ahmed  ·  architecture-explained.png  ·  same figure as v3, with the legend below  ·  14 November 2026",
            13,
            500,
            NAVY2,
            maxw=1550,
        )
        text(W - 56, 1540, "v3  ·  architecture.py", 13, 400, GREY2, "end")

    out.append("</svg>")
    return H


def render(svg: str, png_path: Path, height: int):
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
            f"--window-size={W},{height}",
            f"--screenshot={png_path}",
            html.as_uri(),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    html.unlink(missing_ok=True)


def main():
    for explained, svg_name, png_name in (
        (False, "architecture.svg", "architecture.png"),
        (True, "architecture-explained.svg", "architecture-explained.png"),
    ):
        out.clear()
        warnings.clear()
        _uid[0] = 0
        height = build(explained=explained)
        svg = "\n".join(out)
        (HERE / svg_name).write_text(svg, encoding="utf-8")
        for w_ in warnings:
            print("WARN", w_, file=sys.stderr)
        render(svg, HERE / png_name, height)
        print("wrote", HERE / svg_name, HERE / png_name)


if __name__ == "__main__":
    main()
