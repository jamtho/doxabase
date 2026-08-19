#!/usr/bin/env python3
"""assemble_context v0.5 — budgeted working-memory assembly (doc 17 §3).

v0.5 additions over v0 (each addressing a live-retrieval-trial finding):
- multi-phrasing via pseudo-relevance feedback: the best first-pass hit's
  own vocabulary becomes a second query (the capsule teaches the walk its
  dialect; fixes the documented phrasing-sensitivity failure)
- chunk-level serving: long literals are split and only matching chunks
  served, with the node handle attached (fixes mega-node budget domination)
- schema-tier excluded from serving: classes/shapes are term fuel, never
  items (fixes the generic-label noise that produced the R2 knife-edge)
- two-hop expansion with decay (the associative walk, minimally real)
- honest emptiness: weak entry scores yield "nothing strong" instead of
  noise (keeps context clear; free recall data)
- --describe: what this memory covers, so a consumer knows what it has

Stdlib only; reads the quads table directly and read-only. v1 (true
spreading activation, sleep-built chunk index, embeddings) is designed in
doc 17 and sequenced after the AIS expertise trial.

Usage:
  python3 tools/assemble_context.py CAPSULE.sqlite "task or question"
      [--budget 4000] [--provenance handles|digest|full] [--entries 8]
  python3 tools/assemble_context.py CAPSULE.sqlite --describe
"""
import argparse
import math
import re
import sqlite3
import sys
from collections import defaultdict

TIER = {
    "map": 3.0,
    "patterns": 2.5,
    "observations": 1.5,
    "evidence": 1.0,
    "ontology": 0.8,
}
# Never served as items (term fuel and definitions only):
NEVER_SERVE = {"shapes", "base_ontology", "base_shapes", "history"}
EXCLUDED_GRAPHS = {"history"}

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
HOP2_FACTOR = 0.25
WEAK_FLOOR = 4.0   # below this top score, declare nothing-strong

STOPWORDS = set(
    "the a an and or of to in for on with by from at as is are was were be "
    "been this that these those it its into over under about what which who "
    "how why when where do does did done can could should would may might "
    "will shall must not no nor but if then than so such per each any all "
    "some more most other same own just only very s t d ll re ve using use "
    "used data record records recorded work working".split()
)


def terms_from(text: str):
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower())
    return [w for w in words if w not in STOPWORDS]


def stem(word: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if word.endswith(suf) and len(word) - len(suf) >= 4:
            return word[: -len(suf)]
    return word


def localname(iri: str) -> str:
    return re.split(r"[#/]", iri)[-1] or iri


def chunk_text(text: str, target=550):
    """Split a long literal into readable chunks near target chars,
    merging short paragraphs (the sleep-agent's discretionary chunking is
    v1; this is the cheap deterministic stand-in)."""
    paras = [p.strip() for p in re.split(r"\n\s*\n|(?<=[.;]) (?=\()|(?<=\.) (?=[A-Z(])", text) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if len(cur) + len(p) + 1 <= target or not cur:
            cur = (cur + " " + p).strip()
        else:
            chunks.append(cur)
            cur = p
    if cur:
        chunks.append(cur)
    return chunks


def score_entries(con, terms):
    hit_terms, hit_rows, best_tier = defaultdict(set), defaultdict(int), {}
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
    return {
        s: best_tier[s] * (len(hit_terms[s]) ** 1.5 + math.log1p(hit_rows[s]))
        for s in hit_terms
    }, hit_terms


def node_graph(con, subj):
    r = con.execute(
        "SELECT graph FROM quads WHERE subject=? AND graph NOT IN "
        "('history') LIMIT 1", (subj,)).fetchone()
    return r["graph"] if r else None


def describe(con):
    print("# What this memory covers")
    for g in ("map", "patterns", "observations"):
        rows = con.execute(
            "SELECT object, count(*) FROM quads WHERE graph=? AND "
            "predicate LIKE '%type' AND object_kind='uri' GROUP BY object "
            "ORDER BY 2 DESC LIMIT 12", (g,)).fetchall()
        if rows:
            kinds = ", ".join(f"{localname(o)} ({n})" for o, n in rows
                              if localname(o) not in ("Pattern",))
            print(f"- {g}: {kinds}")
    labels = con.execute(
        "SELECT object FROM quads WHERE graph='map' AND predicate LIKE "
        "'%label' AND object_kind='literal' ORDER BY length(object) "
        "LIMIT 40").fetchall()
    if labels:
        print("- named things include:", "; ".join(r["object"][:60] for r in labels[:25]))
    print("\nConsult this memory with a question whenever you are about to "
          "make a judgement call, are surprised by the data, or are about "
          "to invest effort something like it may have met before.")


def prime(con, entries, args):
    """Push layer (doc 17 + the owner's ladder answer): from the matched
    dataset/domain nodes, serve what the MAP holds about them — every
    linked caveat in full, methods that touch them as a one-line index,
    parameters/invariants as constants. Deep store stays pull-only."""
    seeds = [s for s, _ in entries[:4]]
    print(f"# Priming render (map-tier push)\nseeds: "
          + ", ".join(localname(s) for s in seeds) + "\n")
    seen = set()
    budget_chars = args.budget * 4
    used = 0
    # 1. caveats linked to the seeds (hasKnownCaveat is emitted from the
    #    target side), served in full — trap immunity is cheap and proven.
    cav_subjects = []
    for seed in seeds:
        for row in con.execute(
            "SELECT object FROM quads WHERE subject=? AND predicate LIKE "
            "'%hasKnownCaveat' AND object_kind='uri'", (seed,)):
            if row["object"] not in seen:
                seen.add(row["object"])
                cav_subjects.append(row["object"])
    if cav_subjects:
        print("## Known deficiencies and traps of these tools")
    for c in cav_subjects:
        rows = con.execute(
            "SELECT predicate, object, object_kind FROM quads WHERE "
            "subject=? AND graph NOT IN ('history')", (c,)).fetchall()
        label = next((r["object"] for r in rows
                      if localname(r["predicate"]) == "label"), localname(c))
        texts = [r["object"] for r in rows if r["object_kind"] == "literal"
                 and len(r["object"]) > 40]
        block = f"\n### {label}\n" + "\n".join(f"- {t}" for t in sorted(texts, key=len, reverse=True)[:2]) + "\n"
        if used + len(block) > budget_chars:
            continue
        print(block, end="")
        used += len(block)
    # 2. methods touching the seeds — index only (names + one line);
    #    depth is pull-on-demand.
    heads = []
    for seed in seeds:
        for row in con.execute(
            "SELECT DISTINCT subject FROM quads WHERE object=? AND "
            "object_kind='uri' AND graph IN ('patterns','map')", (seed,)):
            s = row["subject"]
            if s in seen:
                continue
            seen.add(s)
            lab = con.execute(
                "SELECT object FROM quads WHERE subject=? AND predicate "
                "LIKE '%label' LIMIT 1", (s,)).fetchone()
            if lab:
                heads.append((lab["object"], s))
    if heads:
        print("\n## Methods and records that touch these tools "
              "(consult by name for depth)")
        for lab, s in heads[:25]:
            line = f"- {lab}  <{localname(s)}>\n"
            if used + len(line) > budget_chars:
                break
            print(line, end="")
            used += len(line)
    print("\nEverything deeper — episodes, evidence, tuned parameters — "
          "is pull-on-demand: consult with a specific question.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capsule")
    ap.add_argument("task", nargs="?")
    ap.add_argument("--budget", type=int, default=4000)
    ap.add_argument("--provenance", choices=["digest", "handles", "full"],
                    default="handles")
    ap.add_argument("--entries", type=int, default=8)
    ap.add_argument("--describe", action="store_true")
    ap.add_argument("--prime", action="store_true",
                    help="priming mode: treat the task as a dataset/domain "
                         "name; serve the map-tier neighborhood an expert "
                         "would have in mind on picking up these tools — "
                         "caveats in full, methods as an index, constants")
    args = ap.parse_args()

    con = sqlite3.connect(f"file:{args.capsule}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row

    if args.describe:
        describe(con)
        return
    if not args.task:
        sys.exit("task required (or --describe)")

    terms = terms_from(args.task)
    if not terms:
        sys.exit("no usable terms in task description")

    # pass 1
    scores, hit_terms = score_entries(con, terms)
    # pseudo-relevance feedback: best multi-term hit's vocabulary, half weight
    ranked1 = sorted(scores.items(), key=lambda kv: -kv[1])
    prf_terms = []
    for s, sc in ranked1[:3]:
        if len(hit_terms[s]) >= 2:
            lits = con.execute(
                "SELECT object FROM quads WHERE subject=? AND "
                "object_kind='literal' AND graph NOT IN ('history')",
                (s,)).fetchall()
            text = " ".join(r["object"] for r in lits)[:3000]
            freq = defaultdict(int)
            for w in terms_from(text):
                if stem(w) not in {stem(t) for t in terms}:
                    freq[stem(w)] += 1
            prf_terms = [w for w, _ in sorted(freq.items(), key=lambda kv: -kv[1])[:5]]
            break
    if prf_terms:
        scores2, _ = score_entries(con, prf_terms)
        for s, sc in scores2.items():
            scores[s] = scores.get(s, 0) + 0.4 * sc

    entries = sorted(scores.items(), key=lambda kv: -kv[1])[: args.entries]
    top_score = entries[0][1] if entries else 0.0
    # Weakness = low score OR no node matching >=2 distinct query terms
    # (a single common word matching many rows is noise, not memory).
    best_distinct = max((len(hit_terms[s]) for s, _ in entries), default=0)
    if top_score < WEAK_FLOOR or best_distinct < 2:
        print(f"# Working-memory assembly (v0.5)\ntask: {args.task}\n")
        print("MEMORY: nothing strong for this question — the best match "
              f"scored {top_score:.1f} (floor {WEAK_FLOOR}). Candidates "
              "considered: "
              + ", ".join(localname(s) for s, _ in entries[:5])
              + ". Proceed on your own judgement; consider recording what "
                "you learn so the next asker finds it.")
        return

    if args.prime:
        prime(con, entries, args)
        return

    # expansion: 2 hops with decay
    selected = {s: (sc, "entry") for s, sc in entries}
    frontier = list(entries)
    for hop, factor in ((1, 0.5), (2, HOP2_FACTOR)):
        nxt = []
        for subj, sc in frontier:
            for dirn, q in (("→", "SELECT graph, predicate, object AS o FROM quads WHERE subject=? AND object_kind='uri'"),
                             ("←", "SELECT graph, predicate, subject AS o FROM quads WHERE object=? AND object_kind='uri'")):
                for row in con.execute(q, (subj,)):
                    if row["graph"] in EXCLUDED_GRAPHS:
                        continue
                    w = EDGE_WEIGHT.get(localname(row["predicate"]), DEFAULT_EDGE_WEIGHT)
                    cand, s2 = row["o"], sc * factor * w
                    if s2 > selected.get(cand, (0, ""))[0]:
                        selected[cand] = (s2, f"{dirn}{localname(row['predicate'])} (hop {hop})")
                        nxt.append((cand, s2))
        frontier = nxt

    ranked = sorted(selected.items(), key=lambda kv: -kv[1][0])
    floor = ranked[0][1][0] * 0.15
    ranked = [r for r in ranked if r[1][0] >= floor]

    stems = {stem(t) for t in terms} | set(prf_terms)
    out, used = [], 0
    budget_chars = args.budget * 4
    for subj, (sc, why) in ranked:
        g = node_graph(con, subj)
        if g is None or g in NEVER_SERVE:
            continue
        rows = [r for r in con.execute(
            "SELECT graph, predicate, object, object_kind FROM quads "
            "WHERE subject=? ORDER BY predicate", (subj,))
            if r["graph"] not in EXCLUDED_GRAPHS]
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
        if kinds and all(k in ("Class", "Property", "NodeShape", "PropertyShape", "DatatypeProperty", "ObjectProperty") for k in kinds):
            continue  # schema node reached via hops: fuel, not item
        head = label or localname(subj)
        kind = ",".join(k for k in kinds if k not in ("Pattern",))[:60]
        piece = [f"## {head}" + (f"  [{kind}]" if kind else "")]
        if args.provenance in ("handles", "full"):
            piece.append(f"<{subj}>  (score {sc:.1f}, {why})")
        for p, txt in sorted(texts, key=lambda x: -len(x[1]))[:4]:
            if len(txt) <= 650:
                piece.append(f"- {p}: {txt}")
            else:
                chunks = chunk_text(txt)
                scored = []
                for c in chunks:
                    ct = {stem(w) for w in terms_from(c)}
                    scored.append((len(ct & stems), c))
                keep = [c for n, c in sorted(scored, key=lambda x: -x[0]) if n > 0][:3]
                if not keep:
                    keep = [chunks[0]]
                marker = " […] " if len(keep) < len(chunks) else " "
                piece.append(f"- {p} (excerpted {len(keep)}/{len(chunks)} chunks):{marker}" + " […] ".join(keep))
        if args.provenance == "full":
            for p, o in links[:6]:
                piece.append(f"- {p} -> <{o}>")
        block = "\n".join(piece) + "\n"
        if used + len(block) > budget_chars:
            continue
        out.append(block)
        used += len(block)

    print(f"# Working-memory assembly (v0.5)\n"
          f"task: {args.task}\ncapsule: {args.capsule}\n"
          f"budget: ~{args.budget} tokens | mode: {args.provenance} | "
          f"nodes: {len(out)} of {len(ranked)} candidates"
          + (f" | prf: {'+'.join(prf_terms)}" if prf_terms else "") + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
