"""KPI scorecard rendering.

The scorecard never invents numbers. A figure is shown only when a committed
run file under ``eval/results/`` provides it (carrying a UTC timestamp and git
SHA). Otherwise the cell reads ``TARGET`` or ``TO BE MEASURED`` (requirements
R3.4, R8.5; design s11).
"""

from __future__ import annotations

import glob
import json
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_DIR = os.path.join(REPO_ROOT, "eval", "results")

DIMENSIONS = ("completeness", "uniqueness", "consistency", "currentness")
PLACEHOLDER = "TO BE MEASURED"


def latest_scorecard_run(results_dir: str | None = None) -> dict | None:
    """Return the most recent committed scorecard run file, or ``None``."""
    directory = results_dir or RESULTS_DIR
    if not os.path.isdir(directory):
        return None
    candidates = sorted(glob.glob(os.path.join(directory, "*.json")))
    latest = None
    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("kind") == "scorecard":
            latest = data
    return latest


def render_scorecard(results_dir: str | None = None) -> str:
    """Render the scorecard as a Markdown table, placeholders when unmeasured."""
    run = latest_scorecard_run(results_dir)
    lines = ["| Dimension | Figure | Source |", "|---|---|---|"]
    if run is None:
        for dim in DIMENSIONS:
            lines.append(f"| {dim} | {PLACEHOLDER} | — |")
        lines.append(f"| cross-domain key match | {PLACEHOLDER} | — |")
        return "\n".join(lines)
    source = f"{run['generated_at']} @ {run['git_sha']}"
    metrics = run.get("metrics", {})
    for dim in DIMENSIONS:
        value = metrics.get(dim, PLACEHOLDER)
        lines.append(f"| {dim} | {value} | {source} |")
    key_match = metrics.get("cross_domain_key_match", PLACEHOLDER)
    lines.append(f"| cross-domain key match | {key_match} | {source} |")
    return "\n".join(lines)
