"""Render one capsule to a single self-contained HTML report for humans.

The report is an *export artifact*: it carries the shareability banner and a
sensitive-literal scan summary, and stays local pending review (the same
posture as every other export). Usage:

    doxabase-report --capsule project.sqlite --out capsule-report.html

Design notes: single file, no external assets, light/dark via
prefers-color-scheme; status colors always pair with a text label; everything
graph-derived is HTML-escaped.
"""

from __future__ import annotations

import argparse
import html
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from doxabase.core import DoxaBase

_E = html.escape

_CSS = """
:root {
  --page: #f9f9f7; --surface: #fcfcfb; --ink: #0b0b0b; --ink-2: #52514e;
  --muted: #898781; --hairline: #e1e0d9; --accent: #2a78d6;
  --good: #0ca30c; --warning: #fab219; --serious: #ec835a; --critical: #d03b3b;
}
@media (prefers-color-scheme: dark) {
  :root {
    --page: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7;
    --muted: #898781; --hairline: #2c2c2a; --accent: #3987e5;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink);
       font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 980px; margin: 0 auto; padding: 24px 20px 64px; }
h1 { font-size: 22px; margin: 8px 0 2px; }
h2 { font-size: 16px; margin: 36px 0 10px; border-bottom: 1px solid var(--hairline);
     padding-bottom: 6px; }
h3 { font-size: 14px; margin: 18px 0 6px; }
.sub { color: var(--ink-2); font-size: 13px; }
.banner { background: var(--surface); border: 1px solid var(--warning);
          border-radius: 8px; padding: 10px 14px; margin: 16px 0; font-size: 13px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
         gap: 10px; margin: 14px 0; }
.tile { background: var(--surface); border: 1px solid var(--hairline);
        border-radius: 8px; padding: 10px 12px; }
.tile .n { font-size: 22px; font-weight: 650; letter-spacing: -0.01em; }
.tile .l { color: var(--ink-2); font-size: 12px; }
table { border-collapse: collapse; width: 100%; font-size: 13px;
        background: var(--surface); border: 1px solid var(--hairline);
        border-radius: 8px; overflow: hidden; }
th { text-align: left; color: var(--ink-2); font-weight: 600; }
th, td { padding: 6px 10px; border-bottom: 1px solid var(--hairline);
         vertical-align: top; }
tr:last-child td { border-bottom: none; }
.wrap { overflow-x: auto; }
.card { background: var(--surface); border: 1px solid var(--hairline);
        border-radius: 10px; padding: 14px 16px; margin: 12px 0; }
.iri { color: var(--muted); font-family: ui-monospace, monospace; font-size: 11px;
       word-break: break-all; }
.badge { display: inline-block; border-radius: 999px; padding: 1px 9px;
         font-size: 11.5px; font-weight: 600; border: 1.5px solid; }
.badge.minor    { border-color: var(--good);    color: var(--good); }
.badge.moderate { border-color: var(--serious); color: var(--serious); }
.badge.severe   { border-color: var(--critical); color: var(--critical); }
.badge.neutral  { border-color: var(--muted);   color: var(--ink-2); }
.gate { border-left: 3px solid var(--critical); padding: 6px 12px; margin: 8px 0;
        background: var(--surface); border-radius: 0 8px 8px 0; font-size: 13px; }
.gate.none { border-left-color: var(--warning); }
.ok { color: var(--good); font-weight: 600; }
.pattern-links { color: var(--ink-2); font-size: 12.5px; margin: 4px 0 0 0; }
footer { margin-top: 44px; color: var(--muted); font-size: 12px;
         border-top: 1px solid var(--hairline); padding-top: 10px; }
details > summary { cursor: pointer; color: var(--ink-2); font-size: 13px; }
"""


def _severity_badge(severity: Any) -> str:
    if severity is not None and hasattr(severity, "iri"):
        severity = severity.iri
    token = str(severity or "").rsplit("#", 1)[-1].rsplit(":", 1)[-1].lower()
    cls = token if token in {"minor", "moderate", "severe"} else "neutral"
    label = token.capitalize() if token else "Unrated"
    return f'<span class="badge {cls}">&#9679; {label}</span>'


def _tile(value: Any, label: str) -> str:
    return f'<div class="tile"><div class="n">{_E(str(value))}</div><div class="l">{_E(label)}</div></div>'


def _dataset_card(db: DoxaBase, iri: str) -> str:
    d = db.describe_dataset(iri)
    def _ref_name(ref: Any) -> str:
        if ref is None:
            return "—"
        return (ref.label or ref.iri.rsplit("#", 1)[-1]) if hasattr(ref, "iri") else str(ref)

    columns = "".join(
        f"<tr><td>{_E(c.column_name or (c.iri.rsplit('#', 1)[-1]))}</td>"
        f"<td>{_E(_ref_name(c.physical_type))}</td>"
        f"<td>{_E(_ref_name(c.value_type))}</td></tr>"
        for c in d.columns
    )
    caveats = "".join(
        f"<tr><td>{_severity_badge(c.severity)}</td>"
        f"<td>{_E(c.description or '')}"
        + (f"<div class='sub'>Impact: {_E(c.impact)}</div>" if c.impact else "")
        + "</td></tr>"
        for c in d.caveats
    )
    storage_bits = []
    for s in d.storage_accesses:
        root = getattr(s, "storage_root", None) or ""
        proto = getattr(s, "storage_protocol", None)
        if proto is not None and hasattr(proto, "iri"):
            proto = proto.label or proto.iri.rsplit("#", 1)[-1]
        proto = str(proto or "").rsplit("#", 1)[-1]
        storage_bits.append(_E(f"{proto} {root}".strip()))
    layout_bits = []
    for p in d.physical_layouts:
        fmt = getattr(p, "file_format", None)
        if fmt is not None and hasattr(fmt, "iri"):
            layout_bits.append(_E(fmt.label or fmt.iri.rsplit("#", 1)[-1]))
        elif fmt:
            layout_bits.append(_E(str(fmt).rsplit("#", 1)[-1]))
    verification = (
        (d.layout_verification_status.iri.rsplit("#", 1)[-1])
        if d.layout_verification_status
        else "not recorded"
    )
    return f"""<div class="card">
<h3>{_E(d.label or iri.rsplit('#', 1)[-1])} {"<span class='badge neutral'>table</span>" if "Table" in " ".join(getattr(d, "types", []) or []) else ""}</h3>
<div class="iri">{_E(iri)}</div>
<div class="sub">storage: {' · '.join(storage_bits) or '—'} · layout: {' · '.join(b for b in layout_bits if b) or '—'} · verification: {_E(verification)}</div>
<details><summary>{len(d.columns)} column(s)</summary><div class="wrap"><table>
<tr><th>column</th><th>physical</th><th>value type</th></tr>{columns}</table></div></details>
{f'<div class="wrap"><table><tr><th style="width:110px">severity</th><th>caveat</th></tr>{caveats}</table></div>' if caveats else '<div class="sub">No recorded caveats.</div>'}
</div>"""


def _patterns_section(db: DoxaBase) -> str:
    rows = db.list_entities(type="rc:Pattern", graph="patterns", limit=100)
    if not rows.entities:
        return '<div class="sub">No patterns recorded yet.</div>'
    cards = []
    for entity in rows.entities:
        p = db.describe_pattern(entity.iri)
        supports = [s.iri for s in (p.supporting_observations or [])] + [
            s.iri for s in (p.supporting_claims or [])
        ]
        implications = [m.iri for m in (p.map_implications or [])]
        confidence = (
            p.confidence_label
            or str(p.confidence or "").rsplit("#", 1)[-1]
            or "unrated"
        )
        cards.append(
            f"""<div class="card"><h3>{_E(p.label or p.summary or entity.iri.rsplit('#', 1)[-1])}</h3>
<div class="iri">{_E(entity.iri)}</div>
<div>{_E(p.pattern_text or p.summary or '')}</div>
<div class="pattern-links">confidence: {_E(confidence)}
 · supported by {len(supports)} observation/claim(s)
 · {len(implications)} map implication(s)</div>
{f'<div class="iri">→ {_E(", ".join(implications))}</div>' if implications else ''}
</div>"""
        )
    return "".join(cards)


def _revisions_section(db: DoxaBase) -> str:
    listing = db.list_graph_revisions(limit=15)
    if not listing.revisions:
        return '<div class="sub">No revision history yet.</div>'
    rows = "".join(
        f"<tr><td class='sub'>{_E((r.created_at or '')[:19])}</td>"
        f"<td>{_E(r.summary or '')}"
        f"<div class='sub'>{_E((r.application_status or '').replace('_', ' '))}</div></td>"
        f"<td class='sub'>{_E((r.revision_type or '').rsplit('#', 1)[-1])}</td></tr>"
        for r in listing.revisions
    )
    return (
        '<div class="wrap"><table><tr><th style="width:160px">when</th>'
        f"<th>revision</th><th style='width:150px'>type</th></tr>{rows}</table></div>"
    )


def build_capsule_report(db: DoxaBase, *, capsule_name: str = "capsule") -> str:
    brief = db.project_brief(limit=100)
    overview = db.graph_overview(limit=10)
    validation = db.validate_graph(scope="all")
    scan = db.scan_sensitive_literals(limit=5)

    counts = brief.key_counts
    tiles = "".join(
        _tile(counts.get(key, 0), label)
        for key, label in (
            ("datasets", "datasets"),
            ("columns", "columns"),
            ("observations", "observations"),
            ("claims", "claims"),
            ("patterns", "patterns"),
            ("evidence", "evidence"),
            ("graph_revisions", "revisions"),
            ("analysis_packets", "analysis packets"),
        )
    )

    if brief.gates:
        gates = "".join(
            f"<div class='gate {'none' if g.blocks == 'none' else ''}'>"
            f"<strong>{_E(g.gate.replace('_', ' '))}</strong> — blocks {_E(g.blocks)}. "
            f"{_E(g.detail)} <span class='sub'>inspect: {_E(g.details_call)}</span></div>"
            for g in brief.gates
        )
    else:
        gates = '<div class="ok">No gates — nothing is blocked.</div>'

    queues = (
        (
            '<div class="wrap"><table><tr><th>queue</th><th style="width:70px">count</th>'
            "<th>example</th></tr>"
            + "".join(
                f"<tr><td>{_E(q.name.replace('_', ' '))}</td><td>{q.count}</td>"
                f"<td class='iri'>{_E(q.example_iri or '')}</td></tr>"
                for q in brief.queues
            )
            + "</table></div>"
        )
        if brief.queues
        else '<div class="sub">No pending work queues.</div>'
    )

    dataset_cards = "".join(_dataset_card(db, d.iri) for d in brief.datasets)

    validation_line = (
        '<span class="ok">conforms</span>'
        if validation.conforms
        else f'<span class="badge severe">&#9888; {len(validation.results)} violation(s)</span>'
    )
    scan_line = (
        "scanner-clean"
        if scan.match_count == 0
        else f"{scan.match_count} credential-like literal match(es)"
    )
    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    graphs_line = " · ".join(
        f"{g.name} {g.triple_count}" for g in overview.named_graphs if g.triple_count
    )

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DoxaBase capsule report — {_E(capsule_name)}</title>
<style>{_CSS}</style></head>
<body><main>
<h1>Capsule report — {_E(capsule_name)}</h1>
<div class="sub">generated {generated} · SHACL: {validation_line} · sensitive scan: {_E(scan_line)}</div>
<div class="banner">&#9888; <strong>Local-only pending shareability review.</strong>
This report reproduces graph literals faithfully. A clean sensitive-literal scan
is a review prompt, not export approval — review before sharing.</div>

<h2>At a glance</h2>
<div class="tiles">{tiles}</div>
<div class="sub">graphs: {_E(graphs_line)}</div>

<h2>Gates</h2>
{gates}

<h2>Queues</h2>
{queues}

<h2>Datasets ({brief.dataset_count})</h2>
{dataset_cards or '<div class="sub">No datasets recorded.</div>'}

<h2>Patterns</h2>
{_patterns_section(db)}

<h2>Recent revisions</h2>
{_revisions_section(db)}

<footer>DoxaBase capsule report · one static file, no external assets ·
regenerate with <code>doxabase-report --capsule &lt;path&gt;</code></footer>
</main></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a DoxaBase capsule to a single HTML report."
    )
    parser.add_argument("--capsule", default=".doxabase.sqlite")
    parser.add_argument("--out", default="capsule-report.html")
    args = parser.parse_args()
    db = DoxaBase.open_readonly(args.capsule)
    try:
        report = build_capsule_report(db, capsule_name=Path(args.capsule).name)
    finally:
        db.close()
    Path(args.out).write_text(report, encoding="utf-8")
    print(
        f"wrote {args.out} ({len(report):,} chars) - local-only pending "
        "shareability review"
    )


if __name__ == "__main__":
    main()
