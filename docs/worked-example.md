# Worked Example: Inheriting a Capsule Cold

*Human-facing companion to the agent docs. This walks through a real
session — the "transfer test" from the AIS field study
(`docs/journal/trials/2026-07-ais-session-2.md`) — showing the MCP calls
an agent makes, what comes back (abridged), and how it reasons from one
call to the next. The agent here was a deliberately modest model; the
capsule had been built by a stronger one it never met.*

The setup: a cold analyst, three forensics questions about vessels it has
never heard of, and one inheritance — a DoxaBase capsule built by a
previous analyst and corrected by a domain expert. No scratch notes, no
conversation history. The capsule is the whole handover.

---

## Beat 1 — Orient: read the state, not the data

The first call is always the same:

```
→ doxabase.project_brief {"limit": 10}
```
```json
{
  "key_counts": {"datasets": 7, "observations": 41, "claims": 28,
                 "patterns": 17, "evidence": 49, ...},
  "datasets": [
    {"iri": "https://ais.study/dataset/broadcasts",
     "label": "AIS broadcasts (per-message)",
     "column_count": 21, "caveat_count": 10},
    {"iri": "https://ais.study/dataset/daily-index",
     "label": "AIS daily index (per-MMSI per-day summary)",
     "column_count": 28, "caveat_count": 8}, ...],
  "queues": [...], "suggested_next_actions": [...]
}
```

**What the agent took from this**: two real tables, a healthy caveat
count (worth reading before trusting anything), seventeen patterns —
someone has been thinking here. No `gates` key — nothing is blocked, so
read-and-write work may proceed. Cost: ~4k characters.

**Decision**: read the caveats and patterns *before* touching a single
row of data. This is the move that separates inheriting from restarting.

```
→ doxabase.list_entities {"type": "rc:KnownCaveat", "graph": "map"}
→ doxabase.describe_resource {"iri": ".../caveat/timestamp-cet-parse-bug"}
```

The caveat says the `timestamp` column is UTC mis-parsed as CET/CEST and
names `base_date_time` as the trustworthy column. **Every timing claim
the agent makes for the rest of the session uses `base_date_time`** —
one inherited sentence, an entire class of silent errors avoided.

## Beat 2 — Apply: recorded methods are executable inheritance

Task: *which vessels has MMSI 369305000 worked with?* The agent searches
the capsule before inventing anything:

```
→ doxabase.search {"query": "co-movement", "limit": 5}
```
```json
{"matches": [
  {"iri": "https://ais.study/view/co-movement-pairs",
   "label": "M5: persistent co-movement pair detector", ...},
  {"iri": "https://ais.study/query/m5-co-movement-pairs",
   "label": "M5 pair detector SQL (DuckDB)", ...}]}
```

A predecessor left a *method*: a pattern explaining what co-movement
means and why it works, a caveat about same-harbor false pairs, and the
executable SQL. The agent fetched the view, ran the recorded query
filtered to its target, and **reproduced the predecessor's numbers
exactly** — then used the recorded false-pair caveat to dismiss ~19
co-locating vessels as jobsite noise, and filed one borderline case as
"inconclusive" rather than asserting it. Its final answer cites the
method's IRI as evidence.

That is the product thesis in one paragraph: the knowledge moved between
two minds that never met, *with its evidence and its failure modes
attached*, and the weaker mind applied it correctly.

## Beat 3 — Extend: the inheritance lowers the invention threshold

Task: *list the port calls of MMSI 338617000 in May 2024.* No recorded
method covers port calls. But the capsule holds the pieces: a
draft-change method (M4: "draft direction = cargo direction; position
clusters = terminals, no gazetteer needed"), the timestamp caveat, and
index-vs-broadcast cost guidance. The agent composed them into a new
method — screen the cheap daily index for stationary clusters, then
find the exact speed-threshold crossings at broadcast level, then
cross-check draft direction — and recorded it back as **M6**, with its
own caveats and executable SQL, before answering with six terminal
stays, timed and cargo-directional.

The domain expert later confirmed M6's core trick (low-speed dwell
detection) as genuine tradecraft — which the *stronger* predecessor had
not found. The capsule didn't contain the method; it contained enough
for a modest model to build it.

And the traffic ran the other way too: the agent found a case its
predecessor's identity-change method misclassifies (a genuine rename
where neither call sign nor IMO persists), and recorded the gap as a
caveat against the method — with the counterexample as evidence. The
next analyst inherits the method *and* its known blind spot.

## What to notice

- **Nothing here is retrieval-augmented prose.** Every load-bearing
  statement in the agent's answers traces to a graph resource with
  evidence — a caveat IRI, a method IRI, a query that can be re-run.
- **The expensive things happened once.** The strong model paid to
  discover the timestamp bug and build M5; every later session pays a
  few thousand characters to inherit them.
- **Corrections are additive.** The M6 method and the M1 gap-caveat
  entered the capsule the same session; nothing was overwritten; the
  provenance trail shows who knew what, when, from which evidence.

To see the capsule this session inherited and extended, render it:

```
doxabase-report --capsule capsule.sqlite --out report.html
```
