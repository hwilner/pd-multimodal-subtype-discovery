#!/usr/bin/env python
"""Render the Paper 1 demo cross-cohort figure (SVG) from committed artifacts.

Reads ``reports/subtyping_summary.json`` (semi-synthetic validation run --
a documented stand-in built from published summary statistics, NOT real
participant data; see ``docs/DATA_ACCESS.md``) and writes
``reports/paper1/figure2_cross_cohort_demo.svg``: per-held-out-cohort
assignment ARI and subtype-signature correlation, the two pre-registered
reproducibility metrics (``docs/METHODS.md``).

This is the demo-track companion of the planned real-data Figure 2 in
``docs/RESULTS.md`` (authorized by issues #18 -> #15 once the AMP-PD Tier 2
DUA, issue #5, lands). Rendering is deterministic: same artifact ->
byte-identical SVG. No numeric thresholds are drawn because no numeric
reproducibility thresholds have been pre-registered yet (they are fixed in
issue #18); inventing them here would be fabrication.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape

REPO_ROOT = Path(__file__).resolve().parents[2]

# Fixed geometry / palette (no randomness anywhere in this file).
WIDTH, HEIGHT = 640, 320
PANEL_W, PANEL_H = 260, 200
PANEL_Y = 70
PANEL_X = {"ari": 40, "corr": 350}
BAR_W = 60
BAR_GAP = 40
COLORS = ["#2166ac", "#b2182b"]
Y_MAX = 1.05
Y_TICKS = (0.0, 0.25, 0.5, 0.75, 1.0)
DISCLAIMER = "Semi-synthetic stand-in - not real participant data"


def load_summary(reports: Path) -> dict:
    """Load the committed subtyping summary artifact.

    Args:
        reports: Path to the ``reports/`` directory.

    Returns:
        Parsed ``subtyping_summary.json`` dict.

    Raises:
        SystemExit: If the artifact is missing.
    """
    path = reports / "subtyping_summary.json"
    if not path.exists():
        raise SystemExit(f"Missing committed artifact: {path}")
    with open(path) as fh:
        return json.load(fh)


def _fmt(value: float) -> str:
    """Format a metric value to three decimals.

    Args:
        value: Metric value in [0, 1].

    Returns:
        Formatted string, e.g. ``0.950``.
    """
    return f"{value:.3f}"


def _bar_panel(x0: int, title: str, values: dict[str, float]) -> list[str]:
    """Render one bar-panel of the figure as SVG elements.

    Args:
        x0: Left edge of the panel in pixels.
        title: Panel title.
        values: Ordered mapping of cohort name to metric value.

    Returns:
        List of SVG element strings.
    """
    elems = [
        f'<text x="{x0 + PANEL_W / 2:.0f}" y="{PANEL_Y - 12}" '
        f'font-size="13" font-weight="bold" text-anchor="middle">'
        f"{escape(title)}</text>",
    ]
    for tick in Y_TICKS:
        y = PANEL_Y + PANEL_H - tick / Y_MAX * PANEL_H
        elems.append(
            f'<line x1="{x0}" y1="{y:.2f}" x2="{x0 + PANEL_W}" y2="{y:.2f}" '
            f'stroke="#dddddd" stroke-width="1"/>'
        )
        elems.append(
            f'<text x="{x0 - 6}" y="{y + 4:.2f}" font-size="10" '
            f'text-anchor="end">{tick:.2f}</text>'
        )
    bar_x = x0 + BAR_GAP
    for i, (cohort, value) in enumerate(values.items()):
        height = value / Y_MAX * PANEL_H
        y = PANEL_Y + PANEL_H - height
        elems.append(
            f'<rect x="{bar_x}" y="{y:.2f}" width="{BAR_W}" height="{height:.2f}" '
            f'fill="{COLORS[i % len(COLORS)]}"/>'
        )
        elems.append(
            f'<text x="{bar_x + BAR_W / 2}" y="{y - 6:.2f}" font-size="11" '
            f'text-anchor="middle">{_fmt(value)}</text>'
        )
        elems.append(
            f'<text x="{bar_x + BAR_W / 2}" y="{PANEL_Y + PANEL_H + 16}" '
            f'font-size="11" text-anchor="middle">{escape(cohort)}</text>'
        )
        bar_x += BAR_W + BAR_GAP
    elems.append(
        f'<line x1="{x0}" y1="{PANEL_Y + PANEL_H}" x2="{x0 + PANEL_W}" '
        f'y2="{PANEL_Y + PANEL_H}" stroke="#000000" stroke-width="1"/>'
    )
    return elems


def render_figure(summary: dict) -> str:
    """Render the full SVG figure.

    Args:
        summary: Parsed ``subtyping_summary.json`` dict.

    Returns:
        SVG text.
    """
    train = summary["train_cohort"]
    cross = summary["cross_cohort"]
    ari = {c: float(m["assignment_ari"]) for c, m in cross.items()}
    corr = {c: float(m["signature_correlation"]) for c, m in cross.items()}

    elems = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'font-family="Helvetica, Arial, sans-serif">',
        f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>',
        f'<text x="{WIDTH / 2:.0f}" y="24" font-size="14" font-weight="bold" '
        f'text-anchor="middle">Cross-cohort subtype transfer '
        f"(train: {escape(train)})</text>",
        f'<text x="{WIDTH / 2:.0f}" y="42" font-size="11" font-style="italic" '
        f'text-anchor="middle">{DISCLAIMER}</text>',
    ]
    elems += _bar_panel(PANEL_X["ari"], "Assignment ARI vs. in-cohort labels", ari)
    elems += _bar_panel(PANEL_X["corr"], "Subtype-signature correlation", corr)
    elems.append(
        f'<text x="{WIDTH / 2:.0f}" y="{HEIGHT - 10}" font-size="10" '
        f'text-anchor="middle" fill="#555555">Held-out cohorts assigned by '
        f"nearest-centroid (correlation distance). Source: "
        f"reports/subtyping_summary.json.</text>"
    )
    elems.append("</svg>")
    return "\n".join(elems) + "\n"


def main() -> None:
    """Entry point: load the artifact and write the SVG."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reports", type=Path, default=REPO_ROOT / "reports",
                        help="Directory holding the committed artifacts.")
    parser.add_argument("--out", type=Path,
                        default=REPO_ROOT / "reports" / "paper1"
                        / "figure2_cross_cohort_demo.svg",
                        help="Output SVG path.")
    args = parser.parse_args()

    svg = render_figure(load_summary(args.reports))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(svg)
    print(f"Wrote {args.out} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
