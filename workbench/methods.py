"""Method pages: recorded analytical methods rendered as contracts where a
formal one exists, and as L0-only patterns where it does not.

Grounded in the AIS study capsule's actual shape (verified directly against
`/home/codex/ais-study/capsule.sqlite`, doc journal
`docs/journal/trials/knowhow-ab/design-B-capsule.md` -- the winning method-
page design -- amended per `judge-report.md`):

- A "method" is not a typed RDF class. It is one of the capsule's 47
  `rc:Pattern` resources whose `rc:summary` starts "M<n> method" (a naming
  convention, not a graph guarantee -- a future method authored without it
  would not be discovered here; this is a known heuristic, flagged as such,
  not a class the wheel could filter on). Thirteen patterns match today
  (M1-M13).
- Three of the thirteen (M11, M12, M13) additionally have an
  `https://ais.study/mc#MethodContract` resource, reached from the pattern
  by an inbound `mc:forMethod` edge, that formalizes invariants, evidenced
  parameters, realizations, and failure modes. A method page is a page
  about the *pattern* (so all 13 get one), with the contract rendered as an
  enrichment when it exists -- the winning design's own "methods-as-
  patterns" scope, folded in per the build brief.
- `mc:` is entirely project-local; the installed doxabase wheel has zero
  awareness of it (verified: no `MethodContract`/`hasInvariant`/
  `Realization` reference anywhere in `doxabase/core/`). This module reads
  it with direct SQL over `quads`, the same idiom `graph_types.py` and
  `dataset_index.py` already established for "project-specific rollup the
  wheel doesn't cover" -- batched per contract rather than one
  `describe_resource()` call per node (the design doc's own performance
  note: a naive per-node walk is ~25-35 lookups per fully-populated
  contract, tight against the workbench's <100ms floor).

Where the wheel already resolves something cleanly -- pattern text,
supporting claims/evidence with sources, a claim's confidence/observation-
status labels -- this module calls it (`describe_pattern`,
`describe_resource`) rather than re-deriving it from raw triples.
"""
from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from doxabase import DoxaBase, DoxaBaseError, to_dict

from . import frames

# -- Vocabulary -----------------------------------------------------------

RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
RDFS_COMMENT = "http://www.w3.org/2000/01/rdf-schema#comment"
RDFS_SEE_ALSO = "http://www.w3.org/2000/01/rdf-schema#seeAlso"
DCT_SOURCE = "http://purl.org/dc/terms/source"

RC = "https://richcanopy.org/ns/rc#"
RC_PATTERN = RC + "Pattern"
RC_CLAIM = RC + "Claim"
RC_EVIDENCE = RC + "Evidence"
RC_OBSERVATION = RC + "Observation"
RC_DATASET = RC + "Dataset"
RC_TABLE = RC + "Table"
RC_SUMMARY = RC + "summary"
RC_CLAIM_TEXT = RC + "claimText"
RC_PATTERN_TEXT = RC + "patternText"
RC_RATIONALE = RC + "rationale"
RC_PATTERN_TARGET = RC + "patternTarget"
RC_MAP_IMPLICATION = RC + "mapImplication"
RC_CITES_CLAIM = RC + "citesClaim"
RC_HAS_CLAIM = RC + "hasClaim"
RC_EVIDENCE_PRED = RC + "evidence"
RC_SEVERITY = RC + "severity"
RC_IMPACT = RC + "impact"
RC_CAVEAT_DESCRIPTION = RC + "caveatDescription"

MC = "https://ais.study/mc#"
MC_METHOD_CONTRACT = MC + "MethodContract"
MC_FOR_METHOD = MC + "forMethod"
MC_DEPENDS_ON_METHOD = MC + "dependsOnMethod"
MC_HAS_INVARIANT = MC + "hasInvariant"
MC_HAS_PARAMETER = MC + "hasParameter"
MC_HAS_REALIZATION = MC + "hasRealization"
MC_HAS_FAILURE_MODE = MC + "hasFailureMode"
MC_CONSTRAINED_BY = MC + "constrainedBy"
MC_CONSUMES_DATASET = MC + "consumesDataset"
MC_CONSUMES_COLUMN = MC + "consumesColumn"
MC_OUTPUT_GRAIN = MC + "outputGrain"
MC_OUTPUT_MEANING = MC + "outputMeaning"
MC_STATEMENT = MC + "statement"
MC_PARAMETER_ROLE = MC + "parameterRole"
MC_VALUE = MC + "value"
MC_UNIT = MC + "unit"
MC_ENGINE = MC + "engine"

AISNS = "https://ais.study/ns#"
AIS_ASSESSED_AT = AISNS + "assessedAt"
AIS_ASSESSMENT_WINDOW = AISNS + "assessmentDataWindow"

# doc-house convention (verified against all three live contracts):
# rc:summary on a method pattern always starts "M<n> method". A naming
# convention, not a graph guarantee -- see module docstring.
METHOD_LABEL_RE = re.compile(r"^M(\d+)\s+method\b", re.IGNORECASE)

OUTPUT_RELATED_TYPES = {RC_DATASET, RC_TABLE}
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".svg", ".gif")


def _connect(path: Path) -> sqlite3.Connection:
    uri = f"{Path(path).resolve().as_uri()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


# -- Small shared helpers ---------------------------------------------------


def _one(outgoing: dict[str, list[str]], predicate: str) -> str | None:
    values = outgoing.get(predicate)
    return values[0] if values else None


def _outgoing(conn: sqlite3.Connection, subject: str) -> dict[str, list[str]]:
    rows = conn.execute(
        "SELECT predicate, object FROM quads WHERE subject = ?", (subject,)
    ).fetchall()
    out: dict[str, list[str]] = {}
    for predicate, obj in rows:
        out.setdefault(predicate, []).append(obj)
    return out


def _bulk_outgoing(conn: sqlite3.Connection, iris: list[str]) -> dict[str, dict[str, list[str]]]:
    """Every outgoing triple for a batch of subjects, one query -- the
    "handful of batched SQL queries, not N sequential lookups" the design
    doc asks for. Used for invariants/parameters/realizations/failure-modes
    within one contract, and for the second-hop targets their evidence
    chains point at."""
    if not iris:
        return {}
    placeholders = ",".join("?" for _ in iris)
    rows = conn.execute(
        f"SELECT subject, predicate, object FROM quads WHERE subject IN ({placeholders})",
        iris,
    ).fetchall()
    result: dict[str, dict[str, list[str]]] = {}
    for subject, predicate, obj in rows:
        result.setdefault(subject, {}).setdefault(predicate, []).append(obj)
    return result


def _bulk_types(conn: sqlite3.Connection, iris: list[str]) -> dict[str, set[str]]:
    if not iris:
        return {}
    placeholders = ",".join("?" for _ in iris)
    rows = conn.execute(
        f"SELECT subject, object FROM quads WHERE predicate = ? AND subject IN ({placeholders})",
        [RDF_TYPE, *iris],
    ).fetchall()
    types: dict[str, set[str]] = {}
    for subject, obj in rows:
        types.setdefault(subject, set()).add(obj)
    return types


def _local_name(iri: str) -> str:
    return iri.split("#")[-1].split("/")[-1]


def _excerpt(text: str | None, max_chars: int) -> str | None:
    if not text:
        return None
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars].rsplit(" ", 1)[0].rstrip(",;: ")
    return cut + "…"


def _split_sources(sources: list[str]) -> tuple[list[str], list[str]]:
    """(image paths, everything else) from an Evidence resource's
    dct:source values -- extension allow-list only, per the design's plot-
    serving rule; s3://parquet paths and similar render as citations."""
    images: list[str] = []
    other: list[str] = []
    for source in sources:
        (images if source.lower().endswith(IMAGE_EXTENSIONS) else other).append(source)
    return images, other


def _plot_reachable(path: str) -> bool:
    """Whether a recorded evidence source path resolves to a real local
    file under WORKBENCH_DATA_ROOT -- the exact containment check
    `frames.frame_glob` already applies, reused (not reinvented) via the
    now-public `frames.data_root()`. Missing/unreachable is common (plots
    travel with the analysis session's working directory, not the
    capsule) and is not an error: the caller renders an honest fallback
    note instead of a broken `<img>`."""
    root = frames.data_root()
    if root is None or os.path.isabs(path):
        return False
    candidate = os.path.realpath(os.path.join(root, path))
    return candidate.startswith(root + os.sep) and os.path.isfile(candidate)


def _image_entries(paths: list[str]) -> list[dict]:
    return [{"path": p, "reachable": _plot_reachable(p)} for p in paths]


def _method_number(summary: str | None) -> int | None:
    m = METHOD_LABEL_RE.match(summary or "")
    return int(m.group(1)) if m else None


def _short_title(number: int | None, summary: str | None) -> str:
    """'M12 -- per-vessel event-level stops series' -- the header's own
    label, not the raw rc:summary (often 150+ characters of prose). Strips
    the 'M<n> method[ (...)]:' prefix and stops at the design's own
    double-hyphen elaboration marker, or the first full stop for the five
    patterns (M1-M5) that don't use one."""
    if not summary:
        return f"M{number}" if number is not None else "Method"
    m = re.match(r"^M\d+\s+method(?:\s*\([^)]*\))?:\s*(.*)$", summary, re.S)
    rest = m.group(1).strip() if m else summary.strip()
    short = rest.split(" -- ", 1)[0].strip()
    if len(short) > 140:
        short = short[:137].rstrip() + "…"
    prefix = f"M{number} — " if number is not None else ""
    return f"{prefix}{short}"


def _contract_short_label(label: str | None) -> str:
    """'M11' out of 'M11 contract (sketch): physical berth-vs-anchor
    discriminator' -- for the compact 'Also affects: M11' cross-link
    line, not the full title."""
    if not label:
        return "another method"
    m = re.match(r"^(M\d+)\b", label)
    return m.group(1) if m else label


def _depth(contract_iri: str | None, contract_out: dict[str, list[str]] | None) -> str:
    """'full' / 'sketch' / 'none' -- orients, does not grade (steal from
    design A's header, judge-mandated): read directly off which resources
    exist and the contract's own literal words, never a computed
    completeness score. A method with one invariant is not necessarily
    worse-specified than one with five."""
    if not contract_iri or not contract_out:
        return "none"
    text = " ".join(_one(contract_out, RDFS_LABEL) or "" for _ in [0])
    text += " " + (_one(contract_out, RDFS_COMMENT) or "")
    return "sketch" if "sketch" in text.lower() else "full"


DEPTH_BADGE_TEXT = {
    "full": "Full contract",
    "sketch": "Sketch contract",
    "none": "No contract recorded",
}


# -- L0 prose rendering (design B section 3) -------------------------------

_NUMBERED_ITEM_RE = re.compile(r"(?=\(\d+\)\s)")


def _split_l0_heading(paragraph: str) -> tuple[str | None, str]:
    """Detect a leading ALL-CAPS run-in heading such as 'PURPOSE.' or
    'KNOWN BEHAVIOURAL TRADE-OFFS (accepted, not defects):' -- the
    project's in-house contract-comment convention.

    Verified against all three live contracts: the heading's terminator
    varies ('.' on M11/M13, ':' on M12 for the same "TRADE-OFFS" heading)
    and its own parenthetical aside is mixed-case, both of which defeat a
    naive "everything up to the first period must be uppercase" regex (the
    judge-report errata's own noted gap in the source design). Heuristic
    instead: the text up to the first '. '/': ' is a heading only if it is
    short and its first word is itself fully uppercase (PURPOSE, BEHAVIOUR,
    KNOWN, DERIVABILITY, SKETCH, ...) -- distinguishing a heading from an
    ordinary capitalized sentence start ('The method is...'). Falls back to
    no heading (the whole paragraph as body) rather than guessing further;
    never loses text.
    """
    m = re.search(r"[.:]\s+", paragraph)
    if not m:
        return None, paragraph
    prefix = paragraph[: m.start() + 1]
    rest = paragraph[m.end():]
    if len(prefix) > 80:
        return None, paragraph
    first_word = re.match(r"[A-Z]+", prefix)
    if not first_word or len(first_word.group(0)) < 2:
        return None, paragraph
    return prefix, rest


def _split_numbered(body: str) -> list[str] | None:
    if "(1)" not in body:
        return None
    parts = [p.strip() for p in _NUMBERED_ITEM_RE.split(body) if p.strip()]
    if len(parts) < 2:
        return None
    # Safety valve: the split must account for (almost) all of the text --
    # if it doesn't, fall back to one plain paragraph rather than silently
    # dropping content chasing a layout nicety.
    if sum(len(p) for p in parts) < len(body) - 5 * len(parts):
        return None
    return parts


def _parse_l0(text: str | None) -> list[dict]:
    if not text:
        return []
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]
    sections = []
    for paragraph in paragraphs:
        heading, body = _split_l0_heading(paragraph)
        items = _split_numbered(body)
        # Key is "list_items", not "items" -- Jinja resolves `sec.items` to
        # dict.items() (a bound method, shadowing a same-named key) before
        # falling back to __getitem__, so a plain "items" key is
        # unreachable from a template via attribute access.
        sections.append({"heading": heading, "body": None if items else body, "list_items": items})
    return sections


# -- Discovery / identity ---------------------------------------------------


@dataclass(frozen=True)
class MethodRow:
    number: int | None
    pattern_iri: str
    contract_iri: str | None
    title: str
    depth: str
    invariant_count: int
    parameter_count: int
    realization_count: int
    failure_mode_count: int


def _contract_counts(conn: sqlite3.Connection) -> dict[str, dict[str, int]]:
    predicate_names = {
        MC_HAS_INVARIANT: "invariant",
        MC_HAS_PARAMETER: "parameter",
        MC_HAS_REALIZATION: "realization",
        MC_HAS_FAILURE_MODE: "failure_mode",
    }
    placeholders = ",".join("?" for _ in predicate_names)
    rows = conn.execute(
        f"""
        SELECT subject, predicate, COUNT(*) FROM quads
        WHERE predicate IN ({placeholders})
        GROUP BY subject, predicate
        """,
        list(predicate_names),
    ).fetchall()
    counts: dict[str, dict[str, int]] = {}
    for subject, predicate, n in rows:
        counts.setdefault(subject, {})[predicate_names[predicate]] = int(n)
    return counts


def discover_methods(path: Path) -> list[MethodRow]:
    """Every method pattern (M1-M13, the 'M<n> method' summary convention)
    union every mc:MethodContract entity (defensive: a contract whose own
    pattern happens not to match the convention would otherwise be
    invisible). One row each, sorted by method number."""
    conn = _connect(path)
    try:
        summary_rows = conn.execute(
            f"""
            SELECT subject, object FROM quads
            WHERE predicate = ?
              AND subject IN (SELECT subject FROM quads WHERE predicate = ? AND object = ?)
            """,
            (RC_SUMMARY, RDF_TYPE, RC_PATTERN),
        ).fetchall()
        summaries = {
            subject: obj for subject, obj in summary_rows if METHOD_LABEL_RE.match(obj)
        }

        contract_by_pattern = {
            obj: subject
            for subject, obj in conn.execute(
                "SELECT subject, object FROM quads WHERE predicate = ?", (MC_FOR_METHOD,)
            ).fetchall()
        }

        pattern_iris = set(summaries) | set(contract_by_pattern)
        contract_out = _bulk_outgoing(conn, list(contract_by_pattern.values()))
        counts = _contract_counts(conn)

        rows: list[MethodRow] = []
        for pattern_iri in pattern_iris:
            summary = summaries.get(pattern_iri)
            number = _method_number(summary)
            contract_iri = contract_by_pattern.get(pattern_iri)
            c_out = contract_out.get(contract_iri, {}) if contract_iri else None
            depth = _depth(contract_iri, c_out)
            c = counts.get(contract_iri, {}) if contract_iri else {}
            rows.append(
                MethodRow(
                    number=number,
                    pattern_iri=pattern_iri,
                    contract_iri=contract_iri,
                    title=_short_title(number, summary),
                    depth=depth,
                    invariant_count=c.get("invariant", 0),
                    parameter_count=c.get("parameter", 0),
                    realization_count=c.get("realization", 0),
                    failure_mode_count=c.get("failure_mode", 0),
                )
            )
        rows.sort(key=lambda r: (r.number is None, r.number or 0, r.title))
        return rows
    finally:
        conn.close()


def resolve_method(path: Path, iri: str) -> tuple[str, str | None]:
    """Accept either a pattern IRI or a contract IRI (design A's identity
    resolver, folded into B's build) and return (pattern_iri,
    contract_iri | None) -- one canonical method identity regardless of
    which direction a link arrived from."""
    conn = _connect(path)
    try:
        types = {
            row[0]
            for row in conn.execute(
                "SELECT object FROM quads WHERE subject = ? AND predicate = ?", (iri, RDF_TYPE)
            ).fetchall()
        }
        if MC_METHOD_CONTRACT in types:
            row = conn.execute(
                "SELECT object FROM quads WHERE subject = ? AND predicate = ?", (iri, MC_FOR_METHOD)
            ).fetchone()
            return (row[0] if row else iri), iri
        row = conn.execute(
            "SELECT subject FROM quads WHERE object = ? AND predicate = ?", (iri, MC_FOR_METHOD)
        ).fetchone()
        return iri, (row[0] if row else None)
    finally:
        conn.close()


def methods_touching_dataset(path: Path, dataset_iri: str) -> dict:
    """Methods that declare this dataset a contract-scoped input (reverse
    mc:consumesDataset) and methods this dataset itself cites (its own
    outgoing rdfs:seeAlso targets typed mc:MethodContract -- e.g.
    stops-series-full cites both the M12 and M13 contracts, verified) --
    the dataset-page complement of a method page's own Inputs/Output
    sections. Two cheap reverse/forward scans over at most three
    contracts, not a wheel call."""
    conn = _connect(path)
    try:
        consumer_iris = [
            row[0]
            for row in conn.execute(
                "SELECT subject FROM quads WHERE predicate = ? AND object = ?",
                (MC_CONSUMES_DATASET, dataset_iri),
            ).fetchall()
        ]
        cite_candidates = [
            row[0]
            for row in conn.execute(
                "SELECT object FROM quads WHERE subject = ? AND predicate = ?",
                (dataset_iri, RDFS_SEE_ALSO),
            ).fetchall()
        ]
        candidate_types = _bulk_types(conn, cite_candidates)
        citer_iris = [c for c in cite_candidates if MC_METHOD_CONTRACT in candidate_types.get(c, set())]

        contract_iris = list(dict.fromkeys(consumer_iris + citer_iris))
        labels = _bulk_outgoing(conn, contract_iris)

        def _card(contract_iri: str) -> dict:
            return {
                "contract_iri": contract_iri,
                "label": _contract_short_label(_one(labels.get(contract_iri, {}), RDFS_LABEL)),
            }

        return {
            "consumes": [_card(c) for c in consumer_iris],
            "cites": [_card(c) for c in citer_iris],
        }
    finally:
        conn.close()


def method_callout(path: Path, iri: str) -> dict | None:
    """Small {'pattern_iri', 'title'} payload for the generic /resource
    page's "This is method M12 -- open the method page" banner (design A
    §1: specialized pages are opt-in destinations, not silent takeovers of
    the generic view -- the same precedent /resource already follows for
    datasets). None when `iri` is not itself a method pattern or contract."""
    conn = _connect(path)
    try:
        types = {
            row[0]
            for row in conn.execute(
                "SELECT object FROM quads WHERE subject = ? AND predicate = ?", (iri, RDF_TYPE)
            ).fetchall()
        }
        if MC_METHOD_CONTRACT in types:
            row = conn.execute(
                "SELECT object FROM quads WHERE subject = ? AND predicate = ?", (iri, MC_FOR_METHOD)
            ).fetchone()
            pattern_iri = row[0] if row else iri
        elif RC_PATTERN in types:
            pattern_iri = iri
        else:
            return None
        summary = _one(_outgoing(conn, pattern_iri), RC_SUMMARY)
        number = _method_number(summary)
        if number is None:
            return None
        return {"pattern_iri": pattern_iri, "title": _short_title(number, summary)}
    finally:
        conn.close()


# -- Contract sub-sections ---------------------------------------------------


def _param_owner_lookup(conn: sqlite3.Connection, param_iris: list[str]) -> dict[str, str | None]:
    """Reverse mc:hasParameter lookup: which contract owns a parameter IRI
    that isn't in the current contract's own hasParameter set. Judge-
    mandated fix for design B's verified breakage (M13's
    m13-movement-symmetry invariant is constrained by M12's silence-gap
    parameter, reused by reference) -- honest no-owner fallback if the
    reverse lookup ever comes up empty."""
    if not param_iris:
        return {}
    placeholders = ",".join("?" for _ in param_iris)
    rows = conn.execute(
        f"SELECT subject, object FROM quads WHERE predicate = ? AND object IN ({placeholders})",
        [MC_HAS_PARAMETER, *param_iris],
    ).fetchall()
    owners = {obj: subject for subject, obj in rows}
    return {p: owners.get(p) for p in param_iris}


def _invariants(conn: sqlite3.Connection, contract_out: dict[str, list[str]]) -> list[dict]:
    invariant_iris = contract_out.get(MC_HAS_INVARIANT, [])
    if not invariant_iris:
        return []
    bulk = _bulk_outgoing(conn, invariant_iris)
    own_params = set(contract_out.get(MC_HAS_PARAMETER, []))

    all_constrained = list(
        dict.fromkeys(
            p for iri in invariant_iris for p in bulk.get(iri, {}).get(MC_CONSTRAINED_BY, [])
        )
    )
    foreign = [p for p in all_constrained if p not in own_params]
    owner_of = _param_owner_lookup(conn, foreign)
    owner_labels = _bulk_outgoing(conn, [o for o in owner_of.values() if o])
    param_labels = _bulk_outgoing(conn, all_constrained)

    invariants = []
    for iri in invariant_iris:
        po = bulk.get(iri, {})
        constrained = []
        for p in po.get(MC_CONSTRAINED_BY, []):
            label = _one(param_labels.get(p, {}), RDFS_LABEL) or _local_name(p)
            if p in own_params:
                constrained.append({"iri": p, "label": label, "own": True})
            else:
                owner = owner_of.get(p)
                entry = {"iri": p, "label": label, "own": False, "owner_contract_iri": owner}
                if owner:
                    entry["owner_label"] = _contract_short_label(
                        _one(owner_labels.get(owner, {}), RDFS_LABEL)
                    )
                constrained.append(entry)
        invariants.append(
            {
                "iri": iri,
                "label": _one(po, RDFS_LABEL) or _local_name(iri),
                "statement": _one(po, MC_STATEMENT),
                "comment": _one(po, RDFS_COMMENT),
                "constrained_by": constrained,
            }
        )
    return invariants


def _claim_reverse_evidence(conn: sqlite3.Connection, claim_iris: list[str]) -> dict[str, list[str]]:
    """claim_iri -> evidence IRIs reachable one hop through an
    rc:Observation's hasClaim/evidence edges.

    Verified against the live capsule: a claim carries no rc:evidence edge
    of its own (ClaimDescription has no such field, and a raw dump of e.g.
    claim/efe3492a-... confirms it). The image evidence a parameter's
    citesClaim target is backed by lives one hop further out, on an
    Observation that both cites the same claim (rc:hasClaim) and links its
    own evidence (rc:evidence) -- e.g. M11's berth-bound parameters cite
    claim efe3492a-...; observation 0d634bc8-... independently hasClaim's
    that same claim and evidence's the plot-bearing evidence/3325e2de-...
    This is the graph's real "evidence chain" mechanism for a cited claim,
    not an invention -- confirmed for both M11's five radius/hollow-frac/
    heading plots and M13's outage-threshold plot.
    """
    if not claim_iris:
        return {}
    placeholders = ",".join("?" for _ in claim_iris)
    rows = conn.execute(
        f"""
        SELECT hc.object AS claim_iri, ev.object AS evidence_iri
        FROM quads hc
        JOIN quads ev ON ev.subject = hc.subject AND ev.predicate = ?
        WHERE hc.predicate = ? AND hc.object IN ({placeholders})
        """,
        [RC_EVIDENCE_PRED, RC_HAS_CLAIM, *claim_iris],
    ).fetchall()
    result: dict[str, list[str]] = {}
    for claim_iri, evidence_iri in rows:
        result.setdefault(claim_iri, []).append(evidence_iri)
    return result


def _parameters(conn: sqlite3.Connection, db: DoxaBase, contract_out: dict[str, list[str]]) -> list[dict]:
    param_iris = contract_out.get(MC_HAS_PARAMETER, [])
    if not param_iris:
        return []
    bulk = _bulk_outgoing(conn, param_iris)

    all_targets = list(
        dict.fromkeys(
            target
            for iri in param_iris
            for target in bulk.get(iri, {}).get(RC_CITES_CLAIM, [])
            + bulk.get(iri, {}).get(RDFS_SEE_ALSO, [])
        )
    )
    target_types = _bulk_types(conn, all_targets)
    target_out = _bulk_outgoing(conn, all_targets)

    claim_targets = [t for t in all_targets if RC_CLAIM in target_types.get(t, set())]
    reverse_evidence = _claim_reverse_evidence(conn, claim_targets)
    reverse_evidence_iris = list(dict.fromkeys(i for iris in reverse_evidence.values() for i in iris))
    reverse_evidence_out = _bulk_outgoing(conn, reverse_evidence_iris)

    params = []
    for iri in param_iris:
        po = bulk.get(iri, {})
        targets = list(dict.fromkeys(po.get(RC_CITES_CLAIM, []) + po.get(RDFS_SEE_ALSO, [])))

        entries = []
        has_image = False
        has_citation = False
        for target in targets:
            types = target_types.get(target, set())
            t_out = target_out.get(target, {})
            if RC_EVIDENCE in types:
                has_citation = True
                images, other = _split_sources(t_out.get(DCT_SOURCE, []))
                if images:
                    has_image = True
                entries.append(
                    {
                        "kind": "evidence",
                        "iri": target,
                        "summary": _excerpt(_one(t_out, RC_SUMMARY), 320),
                        "images": _image_entries(images),
                        "other_sources": other,
                    }
                )
            elif RC_CLAIM in types:
                has_citation = True
                described = to_dict(db.describe_resource(target, include_incoming=False, limit=5))
                claim = described.get("claim") or {}
                images: list[str] = []
                for evidence_iri in reverse_evidence.get(target, []):
                    imgs, _other = _split_sources(reverse_evidence_out.get(evidence_iri, {}).get(DCT_SOURCE, []))
                    images.extend(imgs)
                if images:
                    has_image = True
                entries.append(
                    {
                        "kind": "claim",
                        "iri": target,
                        "claim_kind_label": claim.get("claim_kind_label"),
                        "confidence_label": claim.get("confidence_label"),
                        "observation_status_label": claim.get("observation_status_label"),
                        "excerpt": _excerpt(claim.get("claim_text"), 380),
                        "images": _image_entries(images),
                    }
                )
            elif RC_OBSERVATION in types:
                has_citation = True
                entries.append(
                    {
                        "kind": "observation",
                        "iri": target,
                        "excerpt": _excerpt(_one(t_out, RC_SUMMARY), 320),
                    }
                )
            elif RC_PATTERN in types:
                entries.append({"kind": "pattern", "iri": target})
            else:
                entries.append({"kind": "other", "iri": target})

        if has_image:
            tier = "surveyed with a plot"
        elif has_citation:
            tier = "documented, not plotted"
        else:
            tier = "no citation recorded beyond the comment"

        params.append(
            {
                "iri": iri,
                "label": _one(po, RDFS_LABEL) or _local_name(iri),
                "comment": _one(po, RDFS_COMMENT),
                "value": _one(po, MC_VALUE),
                "unit": _one(po, MC_UNIT),
                "role": _one(po, MC_PARAMETER_ROLE),
                "assessed_at": _one(po, AIS_ASSESSED_AT),
                "assessment_window": _one(po, AIS_ASSESSMENT_WINDOW),
                "evidence": entries,
                "evidence_tier": tier,
            }
        )
    return params


def _caveat_cross_contract(
    conn: sqlite3.Connection, caveat_iris: list[str], this_contract_iri: str
) -> dict[str, list[dict]]:
    """caveat_iri -> [{iri, short}] for every OTHER contract (among all
    mc:MethodContract entities) that also lists this caveat as a failure
    mode -- the "Also affects: M11" line design B and A both describe.
    One join over the (at most a few dozen) hasFailureMode triples in the
    capsule, not a per-caveat query."""
    if not caveat_iris:
        return {}
    placeholders = ",".join("?" for _ in caveat_iris)
    rows = conn.execute(
        f"SELECT subject, object FROM quads WHERE predicate = ? AND object IN ({placeholders})",
        [MC_HAS_FAILURE_MODE, *caveat_iris],
    ).fetchall()
    by_caveat: dict[str, list[str]] = {}
    for contract, caveat in rows:
        by_caveat.setdefault(caveat, []).append(contract)
    other_contracts = list(
        dict.fromkeys(c for cs in by_caveat.values() for c in cs if c != this_contract_iri)
    )
    labels = _bulk_outgoing(conn, other_contracts)
    result: dict[str, list[dict]] = {}
    for caveat, contracts in by_caveat.items():
        result[caveat] = [
            {"iri": c, "short": _contract_short_label(_one(labels.get(c, {}), RDFS_LABEL))}
            for c in contracts
            if c != this_contract_iri
        ]
    return result


def _failure_modes(
    conn: sqlite3.Connection, contract_iri: str, contract_out: dict[str, list[str]]
) -> list[dict]:
    """Shaped exactly like dataset.html's caveat_card macro expects
    ({iri, label, description, impact, severity: {label}}) plus an
    'also_affects' list -- assembled here (raw traversal, no wheel call
    covers mc:-linked caveats the way describe_dataset() does for
    dataset-linked ones) so the macro import in method.html is a straight
    reuse, not a reimplementation."""
    caveat_iris = contract_out.get(MC_HAS_FAILURE_MODE, [])
    if not caveat_iris:
        return []
    bulk = _bulk_outgoing(conn, caveat_iris)
    severity_iris = list(
        dict.fromkeys(_one(bulk.get(iri, {}), RC_SEVERITY) for iri in caveat_iris if _one(bulk.get(iri, {}), RC_SEVERITY))
    )
    severity_labels = _bulk_outgoing(conn, severity_iris)
    cross = _caveat_cross_contract(conn, caveat_iris, contract_iri)

    modes = []
    for iri in caveat_iris:
        po = bulk.get(iri, {})
        severity_iri = _one(po, RC_SEVERITY)
        severity_label = _one(severity_labels.get(severity_iri, {}), RDFS_LABEL) if severity_iri else None
        modes.append(
            {
                "iri": iri,
                "label": _one(po, RDFS_LABEL) or _local_name(iri),
                "description": _one(po, RC_CAVEAT_DESCRIPTION) or _one(po, RDFS_COMMENT),
                "impact": _one(po, RC_IMPACT),
                "severity": {"label": severity_label} if severity_label else None,
                "also_affects": cross.get(iri, []),
            }
        )
    return modes


def _realizations(conn: sqlite3.Connection, db: DoxaBase, contract_out: dict[str, list[str]]) -> list[dict]:
    realization_iris = contract_out.get(MC_HAS_REALIZATION, [])
    if not realization_iris:
        return []
    bulk = _bulk_outgoing(conn, realization_iris)

    all_see_also = list(
        dict.fromkeys(t for iri in realization_iris for t in bulk.get(iri, {}).get(RDFS_SEE_ALSO, []))
    )
    see_also_types = _bulk_types(conn, all_see_also)

    cards = []
    for iri in realization_iris:
        po = bulk.get(iri, {})
        see_also = po.get(RDFS_SEE_ALSO, [])
        pattern_iri = next((t for t in see_also if RC_PATTERN in see_also_types.get(t, set())), None)
        evidence_iris = [t for t in see_also if RC_EVIDENCE in see_also_types.get(t, set())]

        pattern_text = None
        if pattern_iri:
            # The realization resource itself carries almost nothing --
            # "the code text stays in the pattern; this resource is its
            # identity, not its copy" (its own rdfs:comment, verbatim, on
            # all three realizations). describe_pattern() already resolves
            # patternText cleanly; no hand-parsing needed.
            pattern = to_dict(db.describe_pattern(pattern_iri))
            pattern_text = pattern.get("pattern_text")

        evidence_out = _bulk_outgoing(conn, evidence_iris)
        evidence_cards = []
        for evidence_iri in evidence_iris:
            eo = evidence_out.get(evidence_iri, {})
            images, other = _split_sources(eo.get(DCT_SOURCE, []))
            evidence_cards.append(
                {
                    "iri": evidence_iri,
                    "summary": _excerpt(_one(eo, RC_SUMMARY), 320),
                    "images": _image_entries(images),
                    "other_sources": other,
                }
            )

        cards.append(
            {
                "iri": iri,
                "label": _one(po, RDFS_LABEL) or _local_name(iri),
                "engine": _one(po, MC_ENGINE),
                "comment": _one(po, RDFS_COMMENT),
                "pattern_iri": pattern_iri,
                "pattern_text": pattern_text,
                "evidence": evidence_cards,
            }
        )
    return cards


def _inputs(conn: sqlite3.Connection, contract_out: dict[str, list[str]]) -> list[dict]:
    dataset_iris = contract_out.get(MC_CONSUMES_DATASET, [])
    if not dataset_iris:
        return []
    column_iris = contract_out.get(MC_CONSUMES_COLUMN, [])
    dataset_labels = _bulk_outgoing(conn, dataset_iris)
    column_labels = _bulk_outgoing(conn, column_iris)

    by_dataset: dict[str, list[str]] = {d: [] for d in dataset_iris}
    for column_iri in column_iris:
        # Every column IRI observed is "<dataset IRI>/column/<name>" -- no
        # extra hop needed to find its owning dataset.
        owner = column_iri.split("/column/", 1)[0]
        by_dataset.setdefault(owner, []).append(column_iri)

    groups = []
    for dataset_iri in dataset_iris:
        columns = by_dataset.get(dataset_iri, [])
        groups.append(
            {
                "dataset_iri": dataset_iri,
                "dataset_label": _one(dataset_labels.get(dataset_iri, {}), RDFS_LABEL) or _local_name(dataset_iri),
                "columns": [
                    {"iri": c, "label": _one(column_labels.get(c, {}), RDFS_LABEL) or _local_name(c)}
                    for c in columns
                ],
            }
        )
    return groups


def _output(conn: sqlite3.Connection, contract_iri: str | None, contract_out: dict[str, list[str]], pattern_iri: str) -> dict:
    grain = _one(contract_out, MC_OUTPUT_GRAIN) if contract_out else None
    meaning = _one(contract_out, MC_OUTPUT_MEANING) if contract_out else None

    cited_by: list[dict] = []
    if contract_iri:
        # No mc: predicate for "produces a dataset" exists at all (verified
        # gap, per the design doc): the only honest signal is which dataset
        # resources carry an incoming rdfs:seeAlso back to this contract --
        # labelled as "cites this contract", not "produced by", since the
        # direction isn't uniform across that one predicate (M12's own
        # output, stops-series-full, also cites M13).
        candidates = [
            row[0]
            for row in conn.execute(
                "SELECT subject FROM quads WHERE predicate = ? AND object = ?",
                (RDFS_SEE_ALSO, contract_iri),
            ).fetchall()
        ]
        types = _bulk_types(conn, candidates)
        cited_iris = [c for c in candidates if types.get(c, set()) & OUTPUT_RELATED_TYPES]
        labels = _bulk_outgoing(conn, cited_iris)
        cited_by = [
            {"iri": c, "label": _one(labels.get(c, {}), RDFS_LABEL) or _local_name(c)} for c in cited_iris
        ]

    # Steal from design A: pattern-level output-edge resolution.
    # patternTarget/mapImplication are real edges on the pattern itself, but
    # heavily overloaded (mixing dataset and method-pattern targets under
    # the same predicate) -- resolve by the target's own rdf:type rather
    # than trusting the predicate name; rc:Pattern targets are skipped
    # (already shown as a dependency, not an output). This is a genuinely
    # separate, additional panel from `cited_by` above, not a replacement:
    # it is what recovers M13's feed-outages/stop-boundary-reasons, which
    # carry no mc:-namespace edge back to the contract at all.
    related_datasets: list[dict] = []
    related_other: list[dict] = []
    pattern_out = _outgoing(conn, pattern_iri)
    pattern_targets = list(
        dict.fromkeys(pattern_out.get(RC_PATTERN_TARGET, []) + pattern_out.get(RC_MAP_IMPLICATION, []))
    )
    if pattern_targets:
        types = _bulk_types(conn, pattern_targets)
        labels = _bulk_outgoing(conn, pattern_targets)
        for target in pattern_targets:
            target_types = types.get(target, set())
            if RC_PATTERN in target_types:
                continue
            entry = {"iri": target, "label": _one(labels.get(target, {}), RDFS_LABEL) or _local_name(target)}
            if target_types & OUTPUT_RELATED_TYPES:
                related_datasets.append(entry)
            else:
                related_other.append(entry)

    return {
        "grain": grain,
        "meaning": meaning,
        "cited_by": cited_by,
        "related_datasets": related_datasets,
        "related_other": related_other,
    }


def _dependency_card(conn: sqlite3.Connection, target_pattern_iri: str) -> dict:
    row = conn.execute(
        "SELECT subject FROM quads WHERE predicate = ? AND object = ?",
        (MC_FOR_METHOD, target_pattern_iri),
    ).fetchone()
    contract_iri = row[0] if row else None
    pattern_out = _outgoing(conn, target_pattern_iri)
    summary = _one(pattern_out, RC_SUMMARY)
    depth = "none"
    if contract_iri:
        depth = _depth(contract_iri, _outgoing(conn, contract_iri))
    return {
        "pattern_iri": target_pattern_iri,
        "contract_iri": contract_iri,
        "label": _short_title(_method_number(summary), summary),
        "has_contract": bool(contract_iri),
        "depth": depth,
    }


def _dependencies(conn: sqlite3.Connection, pattern_iri: str, contract_iri: str | None, contract_out: dict[str, list[str]] | None) -> dict:
    depends_on = []
    if contract_out:
        for target in contract_out.get(MC_DEPENDS_ON_METHOD, []):
            depends_on.append(_dependency_card(conn, target))

    # Depended on by: reverse-scan every contract's own dependsOnMethod for
    # an edge pointing at this pattern. Render exactly as recorded -- this
    # is where M12's page shows "depends on: M11" even though M12's own
    # rendered purpose/behaviour text never mentions M11 (a verified
    # anomaly design B asks to be shown honestly, not "corrected").
    rows = conn.execute(
        "SELECT subject, object FROM quads WHERE predicate = ?", (MC_DEPENDS_ON_METHOD,)
    ).fetchall()
    depended_on_by = []
    for subject_contract, target in rows:
        if target == pattern_iri and subject_contract != contract_iri:
            forward = conn.execute(
                "SELECT object FROM quads WHERE subject = ? AND predicate = ?",
                (subject_contract, MC_FOR_METHOD),
            ).fetchone()
            source_pattern = forward[0] if forward else subject_contract
            depended_on_by.append(_dependency_card(conn, source_pattern))

    return {"depends_on": depends_on, "depended_on_by": depended_on_by}


# -- Full page assembly ------------------------------------------------------


def build_method_page(path: Path, db: DoxaBase, iri: str) -> dict:
    pattern_iri, contract_iri = resolve_method(path, iri)
    conn = _connect(path)
    try:
        if contract_iri is None and RC_PATTERN not in _bulk_types(conn, [pattern_iri]).get(pattern_iri, set()):
            raise DoxaBaseError(
                f"'{iri}' is not a recognized method (no mc:MethodContract and not an rc:Pattern)"
            )
        pattern_out = _outgoing(conn, pattern_iri)
        pattern_summary = _one(pattern_out, RC_SUMMARY)
        pattern_rationale = _one(pattern_out, RC_RATIONALE)
        number = _method_number(pattern_summary)
        title = _short_title(number, pattern_summary)

        contract_out: dict[str, list[str]] | None = None
        contract_label = None
        contract_comment = None
        if contract_iri:
            contract_out = _outgoing(conn, contract_iri)
            contract_label = _one(contract_out, RDFS_LABEL)
            contract_comment = _one(contract_out, RDFS_COMMENT)

        depth = _depth(contract_iri, contract_out)

        failure_modes = _failure_modes(conn, contract_iri, contract_out) if contract_out else []
        invariants = _invariants(conn, contract_out) if contract_out else []
        parameters = _parameters(conn, db, contract_out) if contract_out else []
        realizations = _realizations(conn, db, contract_out) if contract_out else []
        inputs = _inputs(conn, contract_out) if contract_out else []
        output = _output(conn, contract_iri, contract_out, pattern_iri)
        dependencies = _dependencies(conn, pattern_iri, contract_iri, contract_out)

        if contract_out:
            l0_sections = _parse_l0(contract_comment)
            l0_source = "contract"
        else:
            l0_sections = []
            l0_source = "pattern"

        # Header "Produces:" line (steal from design A's trust-triage
        # header): the contract's own outputGrain when one exists (short,
        # already one sentence in practice); otherwise the pattern's own
        # summary, since no formal outputMeaning/outputGrain exists for an
        # uncontracted method.
        produces = None
        if contract_out:
            produces = _one(contract_out, MC_OUTPUT_GRAIN) or _one(contract_out, MC_OUTPUT_MEANING)
        if not produces:
            produces = pattern_summary
        produces = _excerpt(produces, 400)

        consumes_labels = None
        if contract_out:
            consumes_labels = [g["dataset_label"] for g in inputs]

        return {
            "pattern_iri": pattern_iri,
            "contract_iri": contract_iri,
            "number": number,
            "title": title,
            "depth": depth,
            "depth_label": DEPTH_BADGE_TEXT[depth],
            "contract_label": contract_label,
            "produces": produces,
            "consumes_labels": consumes_labels,
            "stat_counts": {
                "invariants": len(invariants),
                "parameters": len(parameters),
                "realizations": len(realizations),
                "failure_modes": len(failure_modes),
            },
            "l0_sections": l0_sections,
            "l0_source": l0_source,
            "pattern_summary": pattern_summary,
            "pattern_rationale": pattern_rationale,
            "pattern_text": _one(pattern_out, RC_PATTERN_TEXT),
            "failure_modes": failure_modes,
            "invariants": invariants,
            "parameters": parameters,
            "inputs": inputs,
            "output": output,
            "realizations": realizations,
            "dependencies": dependencies,
        }
    finally:
        conn.close()
