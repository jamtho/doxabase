#!/usr/bin/env python3
"""assemble_context v0 — budgeted working-memory assembly (doc 17 §3).

The simple version: given a capsule and a task description, find entry
points by term match, expand one hop along typed edges, rank by the
epistemic ladder's tier weights, trim to a token budget, and render in
one of three provenance modes. Stdlib only; reads the quads table
directly and read-only. This is the trial instrument, not the product
tool — v1 (spreading activation, decay, a real capsule tool) is
designed in doc 17 and budgeted separately.

Usage:
  python3 tools/assemble_context.py CAPSULE.sqlite "task description..."
      [--budget 4000] [--provenance handles|digest|full] [--entries 8]

Provenance modes (doc 17: a parameter, decided experimentally):
  digest  - clean prose only
  handles - every item carries its IRI so the agent can pull the thread
  full    - handles plus evidence/source edges inline
"""
import argparse
import re
import sqlite3
import sys
from collections import defaultdict

# Ladder-derived tier weights: the map is the reviewed working surface,
# patterns are syntheses, observations are the deep store. History is
# never served (supersession-awareness, the cheap way: the live graphs
# only). Base/seed vocabulary graphs rank below content: definitions
# help orientation but the task usually wants the domain's records.
TIER = {
    "map": 3.0,
    "patterns": 2.5,
    "observations": 1.5,
    "evidence": 1.0,
    "ontology": 0.8,
    "shapes": 0.4,
    "base_ontology": 0.3,
    "base_shapes": 0.2,
}
EXCLUDED_GRAPHS = {"history"}

# Edges worth following out of an entry point, with follow weights.
EDGE_WEIGHT = {
    "supportingObservation": 1.0,
    "citesEpisode": 1.0,
    "fromObservation": 0.9,
    "leadsTo": 0.9,
    "showsFormationOf": 0.9,
    "evidence": 0.7,
    "reexpressedFrom": 0.7,
    "seeAlso": 0.6,
    "relatesToEpisode": 0.6,
}
DEFAULT_EDGE_WEIGHT = 0.4

STOPWORDS = set(
    "the a an and or of to in for on with by from at as is are was were be "
    "been this that these those it its into over under about what which who "
    "how why when where do does did done can could should would may might "
    "will shall must not no nor but if then than so such per each any all "
    "some more most other same own just only very s t d ll re ve".split()
)


def terms_from(task: str):
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", task.lower())
    return [w for w in words if w not in STOPWORDS]


def stem(word: str) -> str:
    """Cheap suffix strip so 'anchored' finds 'anchor', 'stops' 'stop'."""
    for suf in ("ing", "ed", "es", "s"):
        if word.endswith(suf) and len(word) - len(suf) >= 4:
            return word[: -len(suf)]
    return word


def localname(iri: str) -> str:
    return re.split(r"[#/]", iri)[-1] or iri


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capsule")
    ap.add_argument("task")
    ap.add_argument("--budget", type=int, default=4000, help="approx tokens")
    ap.add_argument("--provenance", choices=["digest", "handles", "full"],
                    default="handles")
    ap.add_argument("--entries", type=int, default=8)
    args = ap.parse_args()

    con = sqlite3.connect(f"file:{args.capsule}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    terms = terms_from(args.task)
    if not terms:
        sys.exit("no usable terms in task description")

    # --- entry points: term hits in literals and localnames, live graphs.
    # Score rewards DISTINCT-term coverage over single-term flooding: a
    # node matching three of the task's terms once each should beat a
    # node matching one term fifty times (the M11-vs-M12 lesson from
    # this script's first live test).
    hit_terms = defaultdict(set)   # subject -> set of matched terms
    hit_rows = defaultdict(int)    # subject -> matching row count
    best_tier = {}                 # subject -> best tier weight seen
    for t in terms:
        like = f"%{stem(t)}%"
        for row in con.execute(
            "SELECT graph, subject FROM quads WHERE (object_kind='literal' "
            "AND object LIKE ? COLLATE NOCASE) OR subject LIKE ?",
            (like, like)
        ):
            g = row["graph"]
            if g in EXCLUDED_GRAPHS:
                continue
            s = row["subject"]
            hit_terms[s].add(t)
            hit_rows[s] += 1
            w = TIER.get(g, 0.5)
            if w > best_tier.get(s, 0):
                best_tier[s] = w

    import math
    scores = {
        s: best_tier[s] * (len(hit_terms[s]) ** 1.5 + math.log1p(hit_rows[s]))
        for s in hit_terms
    }
    entries = sorted(scores.items(), key=lambda kv: -kv[1])[: args.entries]
    if not entries:
        sys.exit("no entry points found for these terms")

    # --- one-hop typed expansion, both directions
    selected = {}  # subject -> (score, why)
    for subj, sc in entries:
        selected[subj] = (sc, "entry")
    for subj, sc in entries:
        for row in con.execute(
            "SELECT graph, predicate, object, object_kind FROM quads "
            "WHERE subject=? AND object_kind='uri'", (subj,)
        ):
            if row["graph"] in EXCLUDED_GRAPHS:
                continue
            w = EDGE_WEIGHT.get(localname(row["predicate"]), DEFAULT_EDGE_WEIGHT)
            cand = row["object"]
            s = sc * 0.5 * w
            if s > selected.get(cand, (0, ""))[0]:
                selected[cand] = (s, f"←{localname(row['predicate'])}")
        for row in con.execute(
            "SELECT graph, subject, predicate FROM quads "
            "WHERE object=? AND object_kind='uri'", (subj,)
        ):
            if row["graph"] in EXCLUDED_GRAPHS:
                continue
            w = EDGE_WEIGHT.get(localname(row["predicate"]), DEFAULT_EDGE_WEIGHT)
            cand = row["subject"]
            s = sc * 0.5 * w
            if s > selected.get(cand, (0, ""))[0]:
                selected[cand] = (s, f"→{localname(row['predicate'])}")

    # --- render each selected node compactly, best first, until budget.
    # Relative floor: nodes far below the best hit are vocabulary junk
    # (enum individuals, base classes) that matched a stray term.
    ranked = sorted(selected.items(), key=lambda kv: -kv[1][0])
    if ranked:
        floor = ranked[0][1][0] * 0.15
        ranked = [r for r in ranked if r[1][0] >= floor]
    out, used = [], 0
    budget_chars = args.budget * 4
    for subj, (sc, why) in ranked:
        rows = con.execute(
            "SELECT graph, predicate, object, object_kind FROM quads "
            "WHERE subject=? ORDER BY predicate", (subj,)
        ).fetchall()
        rows = [r for r in rows if r["graph"] not in EXCLUDED_GRAPHS]
        if not rows:
            continue
        label, texts, links, kinds = None, [], [], []
        for r in rows:
            p = localname(r["predicate"])
            if p == "label":
                label = r["object"]
            elif p == "type":
                kinds.append(localname(r["object"]))
            elif r["object_kind"] == "literal" and len(r["object"]) > 15:
                texts.append((p, r["object"]))
            elif r["object_kind"] == "uri" and p in EDGE_WEIGHT:
                links.append((p, r["object"]))
        head = label or localname(subj)
        kind = ",".join(k for k in kinds if k not in ("Pattern",))[:60]
        piece = [f"## {head}" + (f"  [{kind}]" if kind else "")]
        if args.provenance in ("handles", "full"):
            piece.append(f"<{subj}>  (score {sc:.1f}, {why})")
        for p, txt in sorted(texts, key=lambda x: -len(x[1]))[:4]:
            piece.append(f"- {p}: {txt}")
        if args.provenance == "full":
            for p, o in links[:6]:
                piece.append(f"- {p} -> <{o}>")
        block = "\n".join(piece) + "\n"
        if used + len(block) > budget_chars:
            continue
        out.append(block)
        used += len(block)

    print(f"# Working-memory assembly (v0)\n"
          f"task: {args.task}\ncapsule: {args.capsule}\n"
          f"budget: ~{args.budget} tokens | mode: {args.provenance} | "
          f"nodes: {len(out)} of {len(ranked)} candidates\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
