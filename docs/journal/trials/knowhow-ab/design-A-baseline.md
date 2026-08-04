# Method Page Design A — Capsule Workbench

**Author**: design pass, 2026-08-04. **Status**: design for an implementing
session; not built. **Scope**: doc 13 §2 L2 item 5 ("Method pages"), doc 13
open question 2 ("how method pages render two realizations side by side"),
and doc 12's L0–L3 contract layers. Grounded against the live AIS study
capsule (`/home/codex/ais-study/capsule.sqlite`), read directly for this
design — not a fixture, the actual M1–M13 data the workbench must serve.

**Audience for the page itself**: the analyst deciding whether to **trust
and apply** a recorded method to their own question — not the method's
author, who already has the pattern text and the session journal. Every
design choice below is argued from that reader's question, in the order
they'd ask it: *what does this give me → can I believe it → does it apply
to my data → how do I actually run it → what could go wrong.*

---

## 0. What the data actually looks like (read before designing further)

Two facts from the live capsule drive most of the design below; skipping
them produces a page that looks right against a schema diagram and breaks
against the real graph.

**Fact 1 — "a method" is not a typed thing.** The capsule has 47
`rc:Pattern` resources total. Thirteen of them are analytical methods
(M1–M13); the rest are vessel stories and reconciliations, using the exact
same `rc:Pattern` type. There is no `rc:AnalyticalMethod` class. The only
signal is a label/summary convention: `rc:summary` starting `"M<n> method:
..."`. Three of the thirteen — M11, M12, M13 — additionally have an
`mc:MethodContract` resource (cleanly typed) that formalizes them, reached
by `mc:forMethod` (contract → its own pattern) and `mc:dependsOnMethod`
(contract → the pattern of the method it consumes). A **method page is a
page about the pattern**, with the contract rendered as an enrichment when
one exists — not a page about the contract. This is why the task brief
says "a recorded method and its contract": the method (pattern) is always
there; the contract (M11 sketch / M12 full / M13 full) is not.

**Fact 2 — the realization resource is deliberately not the code.** Quoting
the capsule verbatim (`mc:Realization` `rdfs:comment` on all three
realizations): *"The code text stays in the pattern; this resource is its
identity, not its copy."* Every `mc:Realization` in the live capsule has
exactly `rdf:type`, `rdfs:label`, `rdfs:comment`, `mc:engine`, and one or
two `rdfs:seeAlso` (back to the pattern, and to evidence). None carries a
SQL literal. The actual SQL lives embedded in the linked pattern's
`rc:patternText`, as a prose-plus-code block (M12's is ~60 lines of
commented DuckDB SQL with named CTEs). A method page's realization section
is therefore a **pointer-following exercise**, not a field read.

Both facts are stated as fixed inputs, not complaints — doc 12 chose this
shape deliberately (own-resource realizations for "two realizations, one
contract" identity, prose-only code to avoid "no relational algebra in
RDF"). The page design has to work with the graph as authored.

---

## 1. Page identity and routing

- **Route**: `GET /method?iri=<IRI>`, following the existing `resource_url`
  / `dataset_url` convention (`workbench/app.py` registers
  `templates.env.globals["resource_url"]`/`dataset_url"]` the same way; add
  `method_url`).
- **`iri` accepts either the pattern IRI or the contract IRI** and resolves
  to one canonical method identity: if the IRI is an `mc:MethodContract`,
  follow `mc:forMethod` to get the pattern; if it's an `rc:Pattern`, check
  for an inbound `mc:forMethod` to find its contract (may be none). This
  means a link arriving from *any* direction — a contract IRI cited in a
  claim, a pattern IRI found via search, a `dependsOnMethod` target — lands
  on the same page. Implement as one small resolver
  (`workbench/method_index.py::resolve_method(iri) -> (pattern_iri,
  contract_iri | None)`), analogous in spirit to `dataset_index.py`.
- **`/methods` index** (new nav entry, next to Datasets/Types/Revisions in
  `base.html`): every discovered method, one row each — label, contract
  depth badge (see §4), dataset(s) consumed. Discovery = `mc:MethodContract`
  entities (typed, cheap) **union** `rc:Pattern` entities whose
  `rc:summary`/`rdfs:label` matches `^M\d+ method` (a direct `quads` SQL
  scan, same idiom as `graph_types.py`'s "the wheel has no dedicated
  rollup, a GROUP BY here is fine and fast" — document the same way, and
  document the regex as a **known heuristic**, not a graph guarantee: a
  method authored without that label convention would not be found. Flag
  this as a distiller-ledger candidate — `rc:AnalyticalMethod` typing or
  similar — rather than inventing it in this pass; ≥2-domain justification
  is this project's own bar for new ontology, and this is a one-domain
  finding).
- **Generic `/resource` page gets one addition**: when the resource being
  shown is a method pattern or a method contract, render a small callout
  above the existing content — `"This is method M12 — open the method
  page →"` — rather than duplicating the specialized rendering there. This
  mirrors the fact that `/resource` today does *not* special-case datasets
  either (dataset pages are reached via `/datasets` and explicit links, not
  redirect); method pages should follow the same precedent: specialized
  pages are opt-in destinations, not silent takeovers of the generic view.
  The method page itself gets a small footer link back the other way —
  `"View raw triples for this resource →"` — to `/resource?iri=`, so
  nothing is hidden, only specially organized (the project's standing
  transparency rule).

---

## 2. Page structure — what leads

Top to bottom, in the order that answers the trust-then-apply question:

```
┌─────────────────────────────────────────────────────────────┐
│ M12 — per-vessel event-level stops series                    │  <- H1: number + short name, not the IRI
│ [Full contract]  5 invariants · 7 parameters · 1 realization │  <- depth badge, §4
│                                                                │
│ Produces: one row per (mmsi, stop event) — a sub-day-capable  │  <- outputMeaning, 1-2 sentences,
│ interval where SOG stayed below 0.5kn, tolerating short       │     BEFORE any prose wall
│ flickers, terminated by silence >1800s, lasting >=10min.      │
│                                                                │
│ Consumes: broadcasts (mmsi, base_date_time, latitude,         │  <- consumesDataset, linked
│ longitude, sog, heading, status) · depends on: (none formal)  │  <- dependsOnMethod chain
│                                                                │
│ 5 failure modes recorded · evidence: session 12 + 13 surveys  │  <- counts only, detail below
└─────────────────────────────────────────────────────────────┘
```

This header is the entire "should I keep reading" decision surface. It is
deliberately NOT the prose wall (M12's `patternText` is ~60 lines; nobody
should have to read it to decide relevance). Everything in the header is a
short literal pulled straight from `mc:outputMeaning`/`outputGrain` (or, for
uncontracted methods, `rc:summary` — see §8) plus structural counts — no
computed judgement, no invented "quality score."

Below the header, sections in this order (each detailed in §3):

1. **What it does** — full prose (`outputMeaning`, `outputGrain`, and the
   pattern's PURPOSE/BEHAVIOUR text or `rc:summary`/`rc:rationale` for
   uncontracted methods), including the method's own stated known
   trade-offs paragraph where present (M12 and M13 both have one, headed
   "KNOWN BEHAVIOURAL TRADE-OFFS (accepted, not defects)" in the prose —
   render that heading verbatim, it is doing real epistemic work: it is
   the author pre-empting "is this a bug" before the analyst asks).
2. **Inputs and dependencies** — `consumesDataset`/`consumesColumn`, and
   the upstream/downstream method chain.
3. **Invariants** — the checkable promises.
4. **Parameters** — the evidenced thresholds, with plots.
5. **Realizations** — the concrete code, pointer-resolved; N=1 vs N>1.
6. **Failure modes** — reused caveat cards, with shared-caveat cross-links.
7. **Related datasets** — where this method's output actually lands, when
   recorded.
8. Footer: raw-resource link, "authored as" provenance line (`synthesizedAt`,
   confidence/observationStatus/patternStability pills).

Rationale for this order: 1–2 let the analyst rule the method in or out
for their question before paying any cost. 3–5 are the trust layer, in
increasing cost order (an invariant is one sentence; a parameter card
carries a plot; a realization card may require opening a ~60-line SQL
block) — cheapest signal first. 6 is failure modes, deliberately not
first and not last: doc 13's dataset page puts caveats right after the
header ("data never appears without its semantics"); a method page instead
earns the right to state what it does before what can go wrong, because a
method's failure modes are usually about specific populations/edge cases
(M12's dredge-under-merge; M13's gradual-shoulder undercounting), which
read as noise before the analyst has the method's shape in mind. This is
the one place this design intentionally departs from the dataset page's
"caveats first" rule, and it should be revisited if real workbench usage
shows analysts skipping to failure modes anyway (the dataset-page instinct
is well-tested; this is a judgement call, flagged as such).

---

## 3. Section-by-section rendering

### 3.1 What it does

Render `mc:outputMeaning` and `mc:outputGrain` as two short labelled
paragraphs when a contract exists (they are already written as
tight 1-2 sentence statements — M12's `outputGrain` is one sentence, its
`outputMeaning` is one paragraph). Below them, the pattern's own
`rc:patternText`, collapsed by default behind a `<details>`/`<summary>`
disclosure labelled `"Full method description (as authored) — N lines"`
(the SQL lives in here; §3.5 pulls a labelled excerpt out rather than
requiring the analyst to find it in this wall). For methods with a
contract, `patternText` is supplementary detail; for methods without one
(M1–M10, M9 in the worked examples above), `rc:summary` + `rc:rationale`
become the header content and `patternText` is the *only* detail — same
disclosure, not hidden away, just not duplicated as a lead.

L0 stays mandatory per doc 12 §4 — a method page must never suppress the
prose in favor of the structured fields; a contract whose comment
disagrees with its invariants is a bug in the contract, and the page is
where a human would notice that, so both must be visible on one page, not
two clicks apart.

### 3.2 Inputs and dependencies

Table of `mc:consumesDataset` / `mc:consumesColumn` (contract present) —
each row a link via the existing `dataset_url()`/`resource_url()`; group
columns under their dataset. For M12: `broadcasts` (mmsi, base_date_time,
latitude, longitude, sog, heading, status). This is a direct, unambiguous
render — `consumesDataset`/`consumesColumn` are contract-scoped and only
mean one thing.

**Dependency chain** — `mc:dependsOnMethod` (present) resolves to another
method's *pattern* IRI (not a contract IRI — a method can depend on an
uncontracted upstream method, as M11 depends on M7, which has no contract).
Render as a breadcrumb-style chain, resolved recursively up to 3 hops
(cheap: at most 13 methods exist), each hop a `method_url()` link that
still resolves even for the uncontracted end (M7):

```
M7 (no contract)  →  M11 (sketch)  →  M12 (full)  →  M13 (full)
```

Compute **depended-on-by** (downstream) as the reverse edge: scan
`mc:dependsOnMethod` triples across all three contracts for objects
matching this method's pattern IRI (again a direct small quads query, same
scale as `graph_types.py` — 3 contracts total, trivially cheap; do not add
a wheel call for 3 rows). On the real capsule this gives, e.g., M12's page
showing `"Depended on by: M13"`.

**Do not** attempt to resolve `rc:patternTarget`/`rc:mapImplication` as
dependency edges. Both predicates are heavily overloaded on the pre-contract
patterns — M9's pattern uses `patternTarget` to point at a dataset
(`daily-index`), two individual vessel resources, an analysis view, *and*
its upstream method (M7) all under the identical predicate; M12's pattern
mixes dataset targets and method-pattern targets the same way. `mc:`
contract properties exist precisely to replace this ambiguity for the
three contracted methods; reintroducing `patternTarget` parsing into the
method page for dependency edges would resurrect the exact "held together
by convention" problem doc 12 was written to fix. Where `patternTarget`
is still useful is §3.7 (related datasets), where it is filtered by
resolved `rdf:type` rather than trusted by predicate name.

### 3.3 Invariants

One card per `mc:hasInvariant` target: `rdfs:label`, `mc:statement`
(the checkable promise, in full — these are one or two sentences, never
truncate them), and `mc:constrainedBy` parameters as inline pills linking
into §3.4's parameter cards (so an analyst reading "flicker containment"
can jump straight to the flicker-tolerance parameter's evidence).

**Render the `rdfs:comment` prose beneath the statement, not as an
afterthought.** This matters concretely: there is no structured
verification-status field on `mc:Invariant` — no `verifiedAt`,
no boolean pass/fail. The *only* place a check result lives is inside the
comment, as prose the author wrote at authoring time — e.g. M13's
`m13-boundary-completeness` comment: *"Verified exactly on the recorded
output: 60,160,138 = 2 x 30,080,069, with zero duplicate (stop_id,
boundary) pairs."* That sentence **is** the invariant's trust evidence;
hiding it in a tooltip would remove the only check result the graph
carries. Do not attempt to parse it into a computed "PASS" badge — the
text is sometimes a check result (M13's four invariants), sometimes a
design rationale with no check attached (M11's only invariant: "Population-
scale evidence now backs the ambiguous band... forcing it would manufacture
false confidence"), and conflating the two by inventing a badge would
overclaim what the graph actually states. Render the comment as plain body
text under the statement; let the analyst read which kind it is.

This is a real gap worth naming for the distiller ledger (not fixing
here): a structured `mc:verifiedAgainstRun`/`mc:checkResult` pair, cheap to
add and directly checkable, would let the page render an honest pass/fail
pill instead of asking the analyst to parse prose for the word "Verified."
Until it exists, prose-first is the only non-overclaiming choice.

### 3.4 Parameters (the evidence, including plots)

One card per `mc:hasParameter`:

```
┌──────────────────────────────────────────────────────────┐
│ M12 slow-speed threshold              0.5 knot            │  <- label, value+unit
│ Instantaneous slow cutoff: a retained broadcast is 'slow'  │  <- parameterRole
│ exactly when its speed over ground is strictly below this  │
│ value. Applied per broadcast, never to day-level aggregates│
│                                                             │
│ assessed 2026-07-11 · NOAA AIS feed 2024-01-01..2025-12-31;│  <- assessedAt / assessmentDataWindow
│ 457-MMSI stratified sample, 92,454,453 broadcasts,          │
│ 427,134 stop events (session 13)                            │
│                                                             │
│ [cites 1 claim]  ↳ session-13 recall comparison: series     │  <- citesClaim, expanded inline
│   built at 0.5kn exposes the short-stop population the      │     (same rc:Claim rendering as
│   day-index method misses...                                │     resource.html's Claim section)
└──────────────────────────────────────────────────────────┘
```

`mc:value` + `mc:unit` render together as one line (`"0.5 knot"`, `"20
metre"`, `"8 vessels/second"`) — never as two separate table cells; a
number without its unit next to it is a trap on a page whose whole point
is trust. `mc:parameterRole` is the plain-English "what this bounds"
sentence — always render it; it is what lets an analyst who has not read
the full method still understand one threshold in isolation (parameters
are individually linkable from invariant cards, so this must stand alone).

**Do not compute a "survey-backed vs. design-choice" badge from the
comment text.** Several parameter comments say almost exactly that in
prose already — `m12-flicker-tolerance`: *"A design choice, not a
discovered constant: no survey established this value"*; `m13-merge-gap`:
*"same status as M12's flicker tolerance"* — but string-matching for the
phrase "design choice" to synthesize a badge is exactly the kind of
prose-echo fragility this project's own working discipline warns against
(a future author who phrases the same fact differently silently breaks the
badge). Instead render one **honest, structurally-derived** signal: whether
the parameter carries an `rc:citesClaim` link at all. Presence is a real
graph fact (10 of 14 parameters across M11–M13 cite a claim; the 4 that
do not are M12's flicker tolerance, M12's silence gap, M13's merge gap,
and M13's attribution pad — exactly the four whose comment states the
"design choice, not a discovered constant" framing in prose). Label it
plainly: `"cites N claim(s)"` when
present, nothing when absent — no interpretive claim beyond what the graph
states. The comment prose (rendered in full, always) carries the actual
"design choice, not a discovered constant" framing when the author wrote
it; the page's job is to surface that prose, not re-derive a weaker
version of it.

**Plots — the parameter's trust surface (doc 11's own words).** Each cited
claim/evidence is expanded the same way `resource.html`'s existing
`inline_panel` macro already expands claims (reuse it, don't reinvent it —
claim kind/confidence/observationStatus pills + claim text). Additionally,
scan the evidence resource's `dcterms:source` values for image extensions
(`.png`/`.jpg`/`.svg`) and render each as an `<img>`. On the real capsule
this fires for M11's three berth-bound parameters, all citing evidence
`.../7b4cf473-...` and the sibling `.../3325e2de-...` (5 plots:
`m11_a_radius_mean_hist.png` through `m11_e_radius_vs_heading_sd.png`) and
for M13's `outage-threshold` parameter (`m13_outage_threshold_evidence.png`
via claim `c15dada3`).

**Resolving the image is a reachability problem, exactly like the frame
query box's, and should reuse the same primitive.** `dc:source` values are
recorded as working-directory-relative paths from whichever session ran
the analysis (`work/plots/m11_a_radius_mean_hist.png`), not portable URIs —
they are not guaranteed to exist on whatever machine runs the workbench.
`workbench/frames.py::_data_root()` already solves exactly this shape of
problem for local frame files (`WORKBENCH_DATA_ROOT`, default: the
capsule's own directory, with a `os.path.realpath(...).startswith(root +
os.sep)` containment guard). Reuse it verbatim for evidence assets: a new
`workbench/evidence_assets.py` (or a function alongside `_data_root` in
`frames.py`, exported) that (a) rejects any source value containing a URI
scheme (`s3://`, `http://`, ...) — those are not local-servable, render as
plain text; (b) joins the remaining relative path against `_data_root()`;
(c) applies the identical containment check; (d) checks existence at
request time (no long-lived cache — unlike frame reachability, a missing
plot is not worth memoizing across the process). Serve found files via a
new `GET /evidence-asset?path=<relative-path>` route that re-validates
containment server-side (never trust a query param path without
re-checking — this is the one new route in this design that accepts a
filesystem path from the request, so it gets the most scrutiny). When not
found (root unset, or file missing), render the recorded path as plain
text with a one-line note: `"Plot not reachable from this workbench (source
recorded as work/plots/m11_a_radius_mean_hist.png) — see the evidence
resource for the path as recorded."` — the same honest-degradation pattern
the dataset query box already uses for unreachable storage. Verified
against the real capsule: `WORKBENCH_DATA_ROOT` defaulting to
`/home/codex/ais-study` (the capsule's own directory, per the existing
default) resolves `work/plots/m11_a_radius_mean_hist.png` to a real file
that exists on disk today — the happy path is not hypothetical.

### 3.5 Realizations — including two side by side

One card per `mc:hasRealization`: `rdfs:label`, `mc:engine`, the
`rdfs:comment` in full (per §0 fact 2, this comment is often the most
important line on the card — it is where "the code stays in the pattern"
or "two scripts, both windowed/aggregate DuckDB SQL... ~90s over the full
population" lives), and the linked evidence (row counts, timings, sample
sizes — reuse the same evidence rendering as §3.4).

**The SQL itself**: resolve the realization's `rdfs:seeAlso` back to its
pattern, then pull the **same `patternText` disclosure** from §3.1 —
scrolled/anchored to it rather than duplicated as a second copy of a
60-line block. Do not attempt to extract "just the SQL" out of the prose
programmatically (M12's pattern text interleaves prose commentary between
CTEs — "FLICKER MERGE:", "SILENCE BOUNDARY (the bug this session caught):"
— that interleaving is itself trust-relevant content, e.g. it is where the
session-13 defect story lives; stripping it to bare SQL would remove
exactly the narrative that explains why `m12-silence-terminates` exists as
an invariant). Render the whole disclosure, monospaced where it is
clearly code (a simple heuristic — lines starting `WITH`/`SELECT`/four-space
indent — is fine for *styling*, since worst case it just under- or
over-monospaces a paragraph; do not use it for anything that gates
correctness).

**N=1 (today, all three contracts)**: render one card, plus one explicit
sentence: `"1 realization recorded. This contract has not yet been
regenerated against a second engine or approach."` Do not hide the
"compare" affordance behind a conditional that silently disappears when
there is nothing to compare — an analyst who has read doc 12's pitch
("regeneration, cheap transfer...") and lands on a method page should see
that the comparison feature *exists* and know why it is inactive here, not
wonder if it was never built.

**N>1 (designed now, for when it lands)**: doc 12 §7's pilot already
produced exactly this scenario — a blind cold-agent regeneration of M12
reproduced 426,207 vs the original's 427,134 events (−0.22%), all five
invariants passing, per the session-14 trial record — but that regenerated
SQL was never captured as a second `mc:Realization` graph resource, only
narrated in the trial journal. That is the gap this design closes: when a
second realization is staged, the comparison view should render:

```
                    v2 (session 13, canonical)   regenerated (session 14 pilot)
engine              DuckDB SQL                    DuckDB SQL
events              427,134                        426,207  (-0.22%)
flag rate           7.0%                           6.92%
invariants          5/5 (see §3.3)                 5/5 (after determinism fix)
evidence            work/build_stops_series.py     [pilot bundle]
```

concretely: a two-column table, one column per `mc:hasRealization` target
(supports >2 structurally — render N columns — but design/test against 2,
since that's the doc-12 pilot shape and nothing in the vocabulary caps it
at 2), rows = `engine`, then one row per **shared** evidence metric found
on both realizations' cited evidence (row/event counts, flag rates — these
are prose inside `rc:summary`/`dcterms:source`, not structured fields, so
this row set is *whatever numbers both evidence blocks happen to state* —
render the raw evidence summaries side by side rather than trying to
diff-parse numbers out of prose; a human reads two paragraphs faster and
more honestly than a regex misparsing one). The natural place for the
narrative diff ("what the contract failed to say" — doc 12 §7's own
deliverable framing) is a **shared claim or observation targeting both
realizations** via `rc:claimTarget`; if the authoring session records the
comparison that way, the page surfaces it automatically through the
existing claim-target reverse lookup (no new predicate needed — reuse
`rc:claimTarget` exactly as claims already target patterns and datasets
today). If it is not recorded that way, the comparison section still
renders (evidence side by side), just without a synthesized narrative —
graceful degradation again, not a hard requirement on how the second
realization gets authored.

### 3.6 Failure modes

Reuse `dataset.html`'s `caveat_card` macro verbatim (severity-colored left
border, description, impact — already styled, already understood by an
analyst who has seen a dataset page) for every `mc:hasFailureMode` target.
No new visual language.

**One addition specific to methods**: caveats are shared infrastructure,
not per-method copies — `ais-sentinel-values` is a failure mode of *both*
M11 and M12; `m3-silence-is-not-dark` and `missing-day-2024-08-26` are
failure modes of both M12 and M13. Compute this the same cheap way as
§3.2's depended-on-by (a direct quads scan over the (at most a few dozen)
`mc:hasFailureMode` triples in the capsule, not a wheel call), and append
one line under the shared card: `"Also a failure mode of: M11"`. This is
small to build and materially useful — it tells the analyst a caveat is a
structural property of the data (worth understanding once, applies
everywhere) rather than something specific to the method they're currently
reading, which changes how seriously to weight it.

### 3.7 Related datasets

`mc:consumesDataset` already covers inputs (§3.2). For **outputs**, there
is no `mc:producesDataset` in the current vocabulary (another honest gap —
flag for the distiller ledger, do not invent it here) — but the underlying
pattern's `rc:patternTarget`/`rc:mapImplication` links do, in practice,
point at real recorded output datasets: M13's pattern links to
`https://ais.study/dataset/feed-outages` (854 rows, real `rc:Table` with
columns and a row-count snapshot) and `.../dataset/stop-boundary-reasons`.
Since both predicates are overloaded (§3.2), **resolve, don't trust**:
follow every `patternTarget`/`mapImplication` target, fetch its `rdf:type`
via the same cheap one-hop `describe_resource(include_incoming=False,
limit=20)` call `app.py::_expand_inline` already uses for claim/evidence/
caveat inlining (same cap discipline — this list is small, at most a
handful of targets per pattern), and bucket by resolved type:
`rc:Dataset`/`rc:Table` → "Related dataset" (this is where output framing
belongs), `rc:Pattern` → skip (already covered as dependency chain in
§3.2, don't show it twice), anything else (an individual vessel resource,
an analysis view) → "Other related resource," a plain link, no further
claim about the relationship. This is deliberately conservative: it will
under-link before it over-claims, which is the right failure direction on
a page whose entire purpose is trust.

---

## 4. The depth badge

One small, honestly-computed strip in the header, no interpretation:

```
[Full contract]  5 invariants · 7 parameters · 1 realization · 5 failure modes
[Sketch contract]  1 invariant · 3 parameters · 1 realization · 2 failure modes   (M11)
[No contract recorded]  — prose only (rc:summary/patternText)                     (M1-M10, M9 example)
```

"Full"/"Sketch"/"No contract" is read directly off which resources exist
(a contract resource present at all = at least Sketch; the word "sketch"
appears in M11's own label and opening `rdfs:comment` — reuse that literal
distinction by checking for the substrings the two existing contracts
actually use, `"(sketch)"` in the label vs. not, rather than inventing a
third structured field for a distinction the graph already draws in prose
for exactly the one case that needs it today). The counts are plain
`COUNT()`s over `hasInvariant`/`hasParameter`/`hasRealization`/
`hasFailureMode` — no scoring, no "completeness percentage." A method with
1 invariant is not necessarily worse-specified than one with 5; M11 is a
genuinely different, harder problem (three signals, a mandated ambiguous
band) at an earlier stage of contract-writing, and the badge should not
pretend to adjudicate that. It orients ("how much formal structure exists
here to read"), it does not grade.

---

## 5. Navigation to and from other pages

**Into the method page:**
- `/methods` index (new) — the reliable entry point; every method, always
  findable regardless of search ranking.
- Nav bar (`base.html`) — new "Methods" link alongside Datasets/Types/
  Revisions.
- Search — already works today for contracted methods without any change:
  `search("berth anchor discriminator")` surfaces
  `contract/m11-berth-anchor-discriminator` as the top hit by label match.
  It works less reliably for methods identified only by prose (a search for
  "stops series" surfaces evidence resources ahead of the M12 pattern/
  contract, because evidence volume dominates literal-match ranking) — note
  this as a known limitation, not a blocker: `/methods` exists precisely
  because search ranking cannot be the only path in.
- Dataset pages — `dataset.html` should grow a small "Consumed by methods:
  M11, M12" line (the reverse of `mc:consumesDataset`, same cheap-quads-scan
  idiom used throughout this design) next to the existing caveat section.
  This is the single highest-value added link for the "does this method
  apply to my data" question, because it starts from the dataset the
  analyst already has open.
- Failure-mode (caveat) pages — currently plain `/resource` pages; add the
  same "failure mode of: M11, M12" line described in §3.6, symmetric with
  the method page's own rendering of it.
- `dependsOnMethod`/`hasFailureMode`/`consumesDataset` targets anywhere
  else in the app (e.g. a claim's `claimTarget` landing on a method
  pattern) resolve through the existing generic `/resource` page's new
  callout banner (§1).

**Out of the method page:**
- Every `consumesDataset`/`consumesColumn` → `dataset_url()`/`resource_url()`.
- Every parameter's cited claim/evidence → inline-expanded in place (no
  click needed for the common case) plus a link to open it standalone.
- Every failure mode → `resource_url()` (caveats don't have their own
  specialized page in this design; the caveat_card macro already links
  out).
- Dependency chain and depended-on-by → `method_url()` on every hop,
  including the uncontracted end (M7) — this must not dead-end.
- Footer → `resource_url()` for the raw pattern/contract triples.

---

## 6. What is deliberately omitted, and why

- **No computed "trust score."** Every signal on this page (invariant pass
  prose, claim-citation presence, depth counts) is a direct, honestly
  labelled graph fact. Synthesizing them into one number would be the
  single fastest way to make the page lie by omission — the whole point of
  method contracts, per doc 12, is that a threshold's trustworthiness is
  irreducibly about *which* evidence backs it, not a scalar.
- **No live invariant re-checking.** Running an invariant's implied query
  against current data on every page load (to produce a live PASS/FAIL) is
  out of scope: v1 is read-only over static description, doc 13 decision 1
  keeps all execution off the serving path, and — per §3.3 — invariants
  aren't even uniformly formalized as executable checks yet (property-style
  statements in prose, not stored check-queries, per doc 12 §5 decision
  point 1's "start with property-style, promote to executable only where a
  property catches a real regression"). Building a live-check runner ahead
  of that promotion would be solving a problem the contract layer hasn't
  reached yet.
- **No auto-parsed "design choice vs. survey-backed" classification.**
  Explained in §3.4 — the honest structural proxy (citesClaim presence)
  plus full prose is preferred over regex-derived badges that silently
  break when phrasing changes.
- **No `producesDataset` invention.** §3.7 resolves output-dataset links
  from the existing (overloaded) `patternTarget`/`mapImplication`
  predicates by type-filtering rather than proposing a new `mc:` term; new
  vocabulary is out of scope for a page design and belongs in a
  contract-vocabulary v2 pass with its own ≥2-method justification, per
  doc 12 §4's standing rule.
- **No inline realization diff/execution.** Comparing two realizations'
  *behaviour* (re-running both against the same sample and diffing rows)
  is exactly the doc-12 §7 pilot's method, and it is a session activity —
  analysis with judgement — not something a read-only page should attempt
  silently. The comparison view (§3.5) renders whatever evidence/claims a
  session already recorded; it does not generate new ones.
- **No write path.** Consistent with doc 13 decision 1: nothing on this
  page edits a parameter, stages a new realization, or marks an invariant
  checked. It is where the expert decides what to tell their agent next.
- **No vessel/entity-level drill-down from method outputs.** A method page
  is about the method, not a general query surface over what it produced;
  an analyst wanting to inspect actual stop events should follow §3.7's
  "Related dataset" link to `stops-series-full`'s own dataset page and use
  the existing frame query box there. Duplicating query affordances on the
  method page would blur "what is this method" with "let me explore its
  output," which is already a separate, well-built surface.

---

## 7. Acceptance checks (against the real AIS study capsule)

Point `doxabase-workbench /home/codex/ais-study/capsule.sqlite` (matching
`tools/workbench_smoke.sh`'s existing convention of testing against the
real capsule, not a fixture) and check, by IRI, exactly as
`workbench_smoke.sh` already asserts HTTP 200 + expected substrings:

1. **Lead renders from structured fields, not the prose wall.**
   `GET /method?iri=https://ais.study/contract/m12-stops-series` returns
   200 and the response body contains the literal text of
   `mc:outputGrain` ("One row per (mmsi, stop event)") **above** (lower
   byte offset than) the first occurrence of the `patternText` string
   `"STOP-EVENT DEFINITION"` — i.e. the structured summary genuinely
   leads, the 60-line prose block is not the first thing rendered.

2. **Parameter card carries unit-joined value, evidence, and a resolvable
   plot.** The same page contains `"0.5 knot"` (not `"0.5"` and
   `"knot"` in separate, unlabelled places) for
   `param/m12-sog-threshold`, and separately,
   `GET /method?iri=https://ais.study/contract/m11-berth-anchor-discriminator`
   contains an `<img` tag whose resolved `src` serves HTTP 200 for
   `m11_b_hollow_frac_hist.png` when `WORKBENCH_DATA_ROOT=/home/codex/ais-study`
   is set (the real, already-present file), **and**, run again with
   `WORKBENCH_DATA_ROOT` pointed at an empty directory, the same page
   still returns 200 with the fallback text `"Plot not reachable from this
   workbench"` instead of a broken `<img>` or a 500.

3. **Dependency chain resolves through an uncontracted method without
   dead-ending.** `GET /method?iri=https://ais.study/contract/m11-berth-anchor-discriminator`
   returns 200 and contains a link whose resolved target is M7's pattern
   IRI (`.../pattern/208f3abb-...`); following that link
   (`GET /method?iri=https://richcanopy.org/doxabase/generated/pattern/208f3abb-...`)
   also returns 200 (not 404) and its depth badge reads `"No contract
   recorded"`.

4. **Shared failure modes are cross-linked, not silently duplicated.**
   `GET /method?iri=https://ais.study/contract/m12-stops-series` and
   `GET /method?iri=https://ais.study/contract/m11-berth-anchor-discriminator`
   both render a caveat card for `caveat/ais-sentinel-values`, and the M12
   page's card for it contains the substring `"M11"` (the cross-reference
   line from §3.6) — proving the shared-caveat computation actually runs,
   not just that both pages independently list their own `hasFailureMode`
   targets.

5. **N=1 realization renders the explicit not-yet-compared state.**
   `GET /method?iri=https://ais.study/contract/m13-feed-outage-attribution`
   returns 200, shows exactly one realization card
   (`realization/m13-detector-duckdb-v1`) including its `rdfs:comment` in
   full (the "Two scripts, both windowed/aggregate DuckDB SQL..." text),
   and contains the substring `"has not yet been regenerated"` — asserting
   the comparison affordance is present-but-inactive, not silently absent.

---

## 8. Summary for the implementer

New surface: `workbench/method_index.py` (discovery + `resolve_method`,
dependency/failure-mode reverse-edge queries — all direct `quads` SQL in
the established `graph_types.py`/`dataset_index.py` style, since the wheel
has no method rollup), a small evidence-asset resolver reusing
`frames.py::_data_root()`'s exact containment guard, one new route
`GET /method` plus `GET /evidence-asset`, one new route `GET /methods`,
one new template `method.html` (structured per §2–§3, reusing
`caveat_card` from `dataset.html` and `inline_panel`'s claim rendering
from `resource.html` rather than duplicating either), one new template
`methods.html`, a `method_url()` Jinja global, a nav-bar entry, and a
callout addition to the existing `resource.html` and `dataset.html`
templates (§1, §5). No changes to `doxabase/core` — everything here reads
through calls the wheel already exposes (`describe_resource`,
`list_entities`) plus the same class of direct-SQL rollup the workbench
already uses twice.
