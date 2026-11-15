"""`make report` — build the case-study PDF pack (requirements R8.3).

Assembles a PDF from the committed case-study content (``docs/CASE-STUDY.md``)
and embeds the published icon architecture figure
(``docs/diagrams/architecture.png``) — never a Mermaid box-only replacement.

Fails closed:
* a required section is missing from the case study, or
* the results table shows a number with no committed run file under
  ``eval/results/``.

When no committed run file exists, the results stay ``TO BE MEASURED`` and the
report still builds (that is the honest state, not a failure). A number with no
backing run file IS a failure. Standard-library only.
"""

from __future__ import annotations

import os
import re

from . import pdf, scorecard

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASE_STUDY = os.path.join(REPO_ROOT, "docs", "CASE-STUDY.md")
FIGURE = os.path.join(REPO_ROOT, "docs", "diagrams", "architecture.png")
OUT = os.path.join(REPO_ROOT, "report", "case-study.pdf")

# Required sections, mapped to the headings in docs/CASE-STUDY.md.
REQUIRED_SECTIONS = [
    ("Brief", "## 1. Client brief"),
    ("Diagnosis", "## 2. Problem diagnosis"),
    ("Options", "## 3. Options and decision"),
    ("Solution", "## 4. Solution"),
    ("Results", "## 5. Results"),
    ("Roadmap", "## 6. Roadmap and recommendation"),
]


class ReportError(ValueError):
    """Raised when the report cannot be built honestly (fail closed)."""


def _read_case_study() -> str:
    with open(CASE_STUDY, "r", encoding="utf-8") as handle:
        return handle.read()


def _section_text(markdown: str, heading: str, next_heading: str | None) -> str:
    start = markdown.find(heading)
    if start == -1:
        raise ReportError(f"required section missing: {heading}")
    end = markdown.find(next_heading, start + len(heading)) if next_heading else len(markdown)
    if end == -1:
        end = len(markdown)
    return markdown[start:end].strip()


def _check_results_numbers_have_runs(markdown: str) -> None:
    """Fail closed if the Results section shows a numeric figure without a
    committed run file.

    The committed case study uses ``TO BE MEASURED`` placeholders. If a figure
    like ``0.83`` or ``95%`` appears in a results row and no scorecard run file
    exists, that is an invented metric and the report must refuse to build.
    """
    results = _section_text(markdown, "## 5. Results", "## 6. Roadmap and recommendation")
    has_run = scorecard.latest_scorecard_run() is not None
    if has_run:
        return
    # No run file: the results table must not contain a bare number in a row.
    for line in results.splitlines():
        if not line.strip().startswith("|"):
            continue
        if "TO BE MEASURED" in line or "---" in line or "Result" in line:
            continue
        if re.search(r"\b\d+(\.\d+)?%?\b", line):
            raise ReportError(
                "results row contains a number with no committed run file: "
                f"{line.strip()}"
            )


def build_pdf() -> bytes:
    markdown = _read_case_study()

    # Fail closed on missing sections.
    headings = [h for _, h in REQUIRED_SECTIONS]
    for name, heading in REQUIRED_SECTIONS:
        if heading not in markdown:
            raise ReportError(f"required section missing: {name} ({heading})")

    # Fail closed on unsourced numbers in Results.
    _check_results_numbers_have_runs(markdown)

    # Fail closed if the published icon figure is absent or not a PNG we embed.
    if not os.path.exists(FIGURE):
        raise ReportError(f"published architecture figure missing: {FIGURE}")
    with open(FIGURE, "rb") as handle:
        width, height, rgb = pdf.decode_png_rgb(handle.read())

    builder = pdf.PdfBuilder()

    # Title page.
    builder.add_text_page([
        "Enterprise Data Governance & Quality Platform",
        "Case-study pack (oss profile)",
        "",
        "Fictional consultancy: Northwind Advisory",
        "Fictional client: Tarsfeld Group GmbH (synthetic data only)",
        "",
        "This pack is a lab / portfolio artefact. Not legal advice, not a",
        "GDPR / ISO / EU AI Act conformity assessment. Mappings are illustrative.",
        "No metric appears unless a committed run file under eval/results/",
        "provides it (with a UTC timestamp and git SHA).",
    ])

    # Architecture figure page (the published icon figure).
    builder.add_image_page(
        width, height, rgb,
        "Architecture (published icon figure, docs/diagrams/architecture.png). "
        "Generated from architecture.py; not a Mermaid replacement.",
    )

    # One page per required section.
    for idx, (name, heading) in enumerate(REQUIRED_SECTIONS):
        nxt = headings[idx + 1] if idx + 1 < len(headings) else None
        text = _section_text(markdown, heading, nxt)
        lines = [name.upper(), ""] + _markdown_to_lines(text)
        builder.add_text_page(lines)

    # Results / scorecard page straight from committed run files (or placeholders).
    builder.add_text_page([
        "RESULTS (from committed run files only)",
        "",
    ] + scorecard.render_scorecard().splitlines())

    return builder.build()


def _markdown_to_lines(text: str) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        s = line.rstrip()
        if s.startswith("#"):
            s = s.lstrip("#").strip().upper()
        out.append(s)
    return out


def write(out_path: str | None = None) -> str:
    target = out_path or OUT
    os.makedirs(os.path.dirname(target), exist_ok=True)
    data = build_pdf()
    with open(target, "wb") as handle:
        handle.write(data)
    return target


def main() -> int:
    try:
        path = write()
    except ReportError as exc:
        import sys
        print(f"make report failed closed: {exc}", file=sys.stderr)
        return 1
    size = os.path.getsize(path)
    print(f"Wrote {os.path.relpath(path, REPO_ROOT)} ({size} bytes).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
