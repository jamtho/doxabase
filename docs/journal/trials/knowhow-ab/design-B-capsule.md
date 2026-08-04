# Method Page Design (B)

**Author**: product design pass, 2026-08-04. **Scope**: doc 13 §2 L2 item 5
("Method pages: a recorded method rendered as contract... invariants,
evidenced parameters, realizations, dependency graph, failure modes") and
doc 13 §4 open question 2 ("how method pages render two realizations side
by side"). **Status**: design for implementation, not implemented — the
workbench README lists method pages under "Not built."

**Grounding**: every structural claim below was checked against the live
AIS study capsule (`/home/codex/ais-study/capsule.sqlite`) via
`describe_resource`/`describe_pattern`/raw `quads` queries, and against
the shipped `workbench/` code (`app.py`, `resource.html`, `dataset.html`,
`dataset_index.py`, `graph_types.py`, `frames.py`, `style.css`) so this
reads as something that snaps onto the existing app, not a green-field
mock. Concrete IRIs from the real capsule are used throughout so an
implementer can `curl`/`sqlite3` against them directly. The three
contract-bearing methods that exist today:

- `https://ais.study/contract/m11-berth-anchor-discriminator` — labelled
  "sketch" in its own prose, thin (1 invariant, 3 parameters, 1
  never-materialized realization).
- `https://ais.study/contract/m12-stops-series` — complete (5 invariants,
  7 parameters, 1 realization run at full scale, 5 failure-mode caveats).
- `https://ais.study/contract/m13-feed-outage-attribution` — complete (4
  invariants, 4 parameters + 1 reused-by-reference, 1 realization
  producing two output frames, 4 failure-mode caveats).

Designing against all three, not just the richest one, matters: a method
page that only looks good on M12 is a method page that hasn't been
designed, it's been demoed.

---

## 1. Who this page is for, and what that rules out

The brief is explicit: design for the analyst deciding whether to **trust
and apply** a method, not for the method's author. Concretely that means:

- The page's job is to answer, in reading order, "what does this claim to
  do," "where does it break," "why should I believe these numbers," and
  only then "how is it actually computed." An author already knows all
  four; an analyst arrives with none of them and needs them in that
  order, primed to be skeptical before they're shown numbers that look
  authoritative.
- SQL is **verification material for someone going deeper**, not the
  page's subject. Doc 12's whole point is that a contract should be
  readable *without* reading the SQL. The page must not put a code block
  above the fold.
- The page must not invent trust signals the graph doesn't back. No
  synthesized "confidence score" or green-checkmark "passing" badge for
  invariants — nothing in this capsule records a *live* invariant-check
  result (invariants are, per doc 12, "future generated tests"; what
  exists today is prose recording that an invariant was verified once, by
  hand, at authoring time, e.g. "verified exactly on the recorded output:
  9,940,663 movement rows on the start side and 9,940,663 on the end
  side"). Inventing a live-looking check UI over a one-time historical
  claim would manufacture false confidence — exactly the failure mode
  M11's own invariant (`m11-ambiguous-never-forced`) exists to prevent
  in its own domain. The page shows what was verified and when, in the
  contract's own words, never a synthetic status pill.
- Where the graph is silent, thin, or internally inconsistent, the page
  says so plainly rather than smoothing it over. Three concrete examples
  from the live data drive this rule (used again as acceptance checks in
  §8): M12's contract records `dependsOnMethod` pointing at M11's
  pattern even though M12's own prose never mentions M11 and appears to
  have been built directly from broadcasts; M13's two output dataset
  resources (`feed-outages`, `stop-boundary-reasons`) exist and are
  richly described but carry **no graph edge back to the M13 contract**
  at all, only a name-check in free prose; and several parameters have no
  `rc:Evidence` citation, only an `rc:Observation` or a prose comment
  admitting "a design choice, not a discovered constant." An analyst
  making a trust decision needs to see exactly this texture, not a
  page that quietly launders it into uniform-looking rows.

## 2. Page structure — what leads and why

Route: `GET /method?iri=<contract IRI>` (new), paralleling the existing
`/dataset?iri=` / `/resource?iri=` split. Index: `GET /methods` (new),
paralleling `/datasets` and `/types`.

Vertical order, top to bottom, with the justification for each placement
(this is the part of the brief that most needs an explicit argument, not
just a list):

1. **Header** — label, IRI, a `method contract` type pill, and a row of
   stat pills (invariant / parameter / realization / failure-mode /
   dependency counts). Matches the existing `resource.html`/`dataset.html`
   header convention exactly (title, `.iri` monospace line, `.pill` type
   badges) so a method page still *feels* like a workbench page, not a
   bolted-on special case.
2. **Purpose & behaviour (L0)** — the mandatory `rdfs:comment` prose,
   rendered in full, immediately under the header. Doc 12 §4 is explicit
   that L0 is "not residue; it is the layer humans audit" — it has to be
   the first thing read, before any structured claim below it, so a
   disagreement between the prose and the structured L1/L2/L3 content
   (doc 12's own definition of a contract bug) is something the reader
   can actually notice.
3. **Failure modes** — directly after the purpose prose, *before*
   invariants or parameters. This mirrors an existing, shipped precedent
   exactly: `dataset.html` puts its "Caveats — data never appears without
   its semantics" section immediately after the header pills, before the
   Columns table (`workbench/templates/dataset.html:33-39`). Method pages
   should carry the same law: an analyst should trip over what can go
   wrong before they see numbers that look authoritative. Doc 13 §2 lists
   failure modes last in its own bullet, but that's an enumeration, not a
   layout instruction, and the shipped dataset-page precedent is the
   stronger, load-bearing signal to follow for consistency.
4. **Invariants** — the checkable promises. Read after failure modes (the
   known ways the method fails on purpose) and before parameters (the
   numbers), invariants set up "what has to be true" so the parameter
   section that follows reads as "and here's what was tuned to make it
   true," not as a bare list of numbers.
5. **Parameters, with evidence** — the flagship section (see §4). Deepest
   and longest section on the page by design; this is the "trust surface"
   doc 13 names explicitly.
6. **Inputs & Output** — grounding in the described world: consumed
   datasets/columns (linking straight into the existing dataset/resource
   pages), then the contract's own `outputGrain`/`outputMeaning` prose.
   Placed after the trust-building sections deliberately — an analyst who
   has already decided to distrust the method doesn't need to read what
   it consumes.
7. **Realizations** — the SQL, gated behind a `<details>` disclosure (see
   §5). Last among content sections on purpose.
8. **Dependencies** — depends-on / depended-on-by, linking to neighbouring
   method pages. Positioned as cross-navigation at the end, not as
   content about *this* method.

No History section is proposed as required scope (unlike `resource.html`,
which already has one) — see §7 for why it's a deliberate omission rather
than an oversight.

## 3. Purpose & behaviour (L0) rendering

The recorded contracts are not unstructured paragraphs — M12 and M13's
comments are hand-written with a consistent in-house convention:
ALL-CAPS section labels (`PURPOSE.`, `BEHAVIOUR, in order.`, `KNOWN
BEHAVIOURAL TRADE-OFFS (accepted, not defects).`, `DERIVABILITY.`) each
starting a paragraph, and `BEHAVIOUR`'s own paragraph is itself a
numbered list `(1) ... (2) ... (3) ...`. Render this structure instead of
dumping one text blob:

- Split the comment on blank lines into paragraphs.
- If a paragraph's first ~40 characters match `^[A-Z][A-Z ,]+\.` (a
  leading run of capitals ending in a period), render that leading phrase
  as a bold/small-caps run-in label and the rest of the paragraph as body
  text.
- Within a paragraph, if it contains `(1)`, `(2)`, `(3)`... as
  sentence-leading markers, render as an ordered list (regex split on
  `(?=\(\d+\)\s)`; still safe to fall back to one plain paragraph if the
  split doesn't cleanly account for the whole string — never lose text
  trying to be clever about layout).

This is a formatting nicety, not new information — the M11 contract's
literal first line ("SKETCH (L1 outline; the full contract is future
work).") becomes the first thing rendered on the page in this scheme,
which is exactly the honesty signal §1 asks for: no synthetic maturity
score, just the author's own words rendered where they can't be missed,
next to the stat-pill counts that let the reader corroborate or doubt
them structurally.

## 4. Invariants

One card/row per invariant (`mc:hasInvariant` targets), each rendering:

- **Statement** (`mc:statement`) — the actual checkable claim, e.g. "No
  stop event contains an internal reporting silence longer than the
  silence gap parameter."
- **Why this exists** (`rdfs:comment`) — often a regression story, not
  abstract rationale: M12's `m12-silence-terminates` comment literally
  says "the first implementation kept same-state runs joined across long
  silences and assembled a 70-day 'stop' from 47 messages. A regenerated
  realization that fails this check has reproduced that bug." This
  sentence is *more* trust-relevant to an analyst than the formal
  statement above it — render it, don't relegate it to a tooltip.
- **Constrained by** (`mc:constrainedBy` → parameter IRIs) — see the
  cross-method reuse handling below.

**Cross-method parameter reuse** (a real, verified case, not a
hypothetical): M13's `m13-movement-symmetry` invariant is constrained by
`https://ais.study/param/m12-silence-gap` — a parameter that belongs to
*M12's* `hasParameter` list, not M13's own four. M13's contract text says
this explicitly ("M12's own silence-gap parameter, reused by reference,
not redefined"), and the know-how capsule's own harvested episode names
this as the intended sharing form ("shared EVIDENCE is cited while
parameter RESOURCES stay duplicated... M13 reuses M12's silence-gap
parameter by reference"). The renderer must not silently show this as if
it were one of M13's own parameters. Algorithm: for each `constrainedBy`
target, check membership in the current contract's own `hasParameter`
set; if absent, do one more cheap reverse query (`SELECT subject FROM
quads WHERE predicate = mc:hasParameter AND object = <param IRI>`) to
find the owning contract, and render "constrained by `m12-silence-gap`
(defined in the **M12** contract, reused here by reference) →" linking to
that contract's page, not a duplicate card. If no owning contract is
found (shouldn't happen today, but design for it), render "no owning
contract found for this parameter" rather than crashing or fabricating
one.

No status pill on invariants (§1). The one thing worth surfacing as a
distinct, small badge is whether the comment text contains an exact
verified count (a regex for a number followed by "rows"/"events" near
the word "verified"/"exactly" is enough to flag "verified with a numeric
check" vs. plain prose) — genuinely optional polish, not required for v1.

## 5. Parameters, with evidence — the flagship section

Doc 13's own words: "evidenced parameters (plots inline — the session-12
threshold plots ARE the parameter's trust surface)." This is the section
worth building carefully.

**Card per parameter** (`mc:hasParameter` targets), each showing:

- **Value + unit**, large/prominent (`mc:value`, `mc:unit`) — e.g. `20
  metre`, `0.5 knot`, `8 vessels/second`.
- **Role** (`mc:parameterRole`) — what the value is actually gating,
  often itself informative about softness ("A soft threshold, never a
  hard cutoff").
- **Provenance strip**: `assessedAt` / `assessmentDataWindow`. These are
  literally the same `https://ais.study/ns#assessedAt` /
  `.../assessmentDataWindow` predicates the *existing* anchored-derivation
  panel on `resource.html` already renders for doc-14 provenance
  (`workbench/app.py`'s `_ANCHORED_DERIVATION_PREDICATES`). Reuse that
  rendering treatment (the same "indexical, not timeless" framing line),
  don't invent a second one — the project already decided what this kind
  of provenance looks like.
- **Evidence chain**: walk `rc:citesClaim` and `rdfs:seeAlso` targets and
  branch on the target's `rdf:type`:
  - **`rc:Evidence`**: pull its `sources` list (the wheel's
    `EvidenceDescription.sources`, already resolved cleanly — no need to
    hand-parse `dct:source` triples). Any source whose extension is
    `.png`/`.jpg`/`.jpeg`/`.svg`/`.gif` renders as an inline `<img>` (see
    plot-serving below); everything else (parquet/S3 paths) renders as a
    small monospace citation list, not an image attempt. Caption: the
    evidence's own `rc:summary`, truncated to ~2 sentences with a "Read
    the full evidence note →" link to the evidence's own resource page
    for the rest (these summaries run to 2-4k characters — M11's radius
    survey evidence note is a full incident report about a GPS-glitch
    population; excellent material, wrong place to dump in full on every
    parameter card).
  - **`rc:Claim`**: confidence pill + observation-status pill (already
    have label-resolved forms via `describe_resource`) + a ~300-400
    character excerpt of `claimText` (first sentence or two) + "Read the
    full claim →". Claims run even longer than evidence notes (the
    M11 population-survey claim is ~4,700 characters) — same rule.
  - **`rc:Observation`**: same excerpt-and-link treatment. Render
    plainly; don't try to detect "this is a design-choice observation"
    by string-matching — M12's flicker-tolerance parameter's own comment
    already says outright "A design choice, not a discovered constant. No
    survey established this value," and that sentence is *itself* part
    of the rendered comment (§ above) or the observation excerpt. Let the
    prose say it; don't paraphrase it into a badge that can drift out of
    sync with the prose.
  - Anything else (e.g. a `rc:Pattern` target, which several parameters'
    `seeAlso` also points at) — a plain link, no card. The pattern is
    already reachable from the Realizations section; don't duplicate its
    5000-character text here.

**Evidence-tier signal**: rather than compute a subjective "how well
validated is this" score, show only what's structurally true — whether
at least one linked `rc:Evidence` resource carries an image-extension
source (i.e., "surveyed with a plot") vs. only `rc:Claim`/`rc:Observation`
citations (i.e., "documented, not plotted") vs. (shouldn't occur today,
but handle it) no citation at all beyond the comment. Three small,
factual labels, computed from what's actually linked — no invented
weighting.

### Plot serving

The plot files are **not** servable today — they're local files
(`work/plots/*.png`) referenced by relative path in `dct:source`
literals, and they genuinely exist on disk (verified:
`/home/codex/ais-study/work/plots/m11_a_radius_mean_hist.png` and five
siblings, plus `m13_outage_threshold_evidence.png` and
`recall_by_duration_bucket.png`), relative to the *same directory the
capsule file itself lives in* — exactly the existing `WORKBENCH_DATA_ROOT`
convention `workbench/frames.py`'s `_data_root()` already implements
("default: the capsule's own directory"). Reuse that function (promote it
out of `frames.py` into a small shared helper, or duplicate its six lines
into a new `workbench/evidence.py` module alongside `dataset_index.py`/
`graph_types.py`) rather than inventing a second root-resolution
convention.

New route: `GET /evidence/plot?path=work/plots/m11_a_radius_mean_hist.png`
— resolves the path against the data root with the same
`os.path.realpath(...).startswith(root + os.sep)` containment check
`frame_glob` already uses, allow-lists image extensions only, serves the
bytes with a long `Cache-Control` (capsule is read-only for the life of
the process) and a plain `Content-Type` guessed from the extension.
Missing file (common — evidence rows travel with the capsule, the
`work/plots/` directory usually doesn't) is **not** an error page: render
the citation as plain text with a small "plot referenced, not found
locally at `<path>`" note, matching the existing "This dataset's storage
is not reachable right now" honest-fallback pattern used on dataset
pages, rather than a broken-image icon.

## 6. Inputs & Output

**Inputs**: group `mc:consumesColumn` targets by their owning dataset
(derivable from the column IRI's own path — every column IRI observed is
`<dataset IRI>/column/<name>`; no extra hop needed) under each
`mc:consumesDataset` target. If a declared `consumesDataset` has zero
matching `consumesColumn` entries (true today for M11 and M12's
`daily-index` — both declare it as a consumed dataset but list no
individual columns from it), show it plainly as "dataset consumed, no
individual columns declared" rather than hiding the mismatch. Column
links use the existing `resource_url()` helper (they already render fine
as generic resource pages); dataset links use `dataset_url()` straight
into the existing, richer dataset page — this section should feel like a
bridge into the frame browser, not a copy of it.

**Output**: render `mc:outputGrain` and `mc:outputMeaning` in full — this
prose is the *only* reliable description of what a method produces today.
Do not attempt to assert a formal "produces" edge to dataset resources:
checked directly against the graph, **no `mc:` predicate for output
datasets exists at all**. M12's output (`stops-series-full`) happens to
be reachable because the dataset itself carries an `rdfs:seeAlso` back to
the M12 contract (visible today as an *incoming* triple on the contract's
resource page) — but M13's two output frames
(`https://ais.study/dataset/feed-outages`,
`https://ais.study/dataset/stop-boundary-reasons`) carry **no edge back
to the M13 contract whatsoever**, only a name-check inside their own free
text ("Realized by work/m13/build_feed_outages.py... recorded via the
M13 contract/pattern"). Design for what's actually there: a secondary
**"Related datasets"** panel lists whatever `rc:Dataset`/`rc:Table`
resources have an incoming `rdfs:seeAlso` to this contract (a
one-hop scan of the contract's own incoming triples, already computed by
`describe_resource`), labelled honestly as *"datasets that cite this
contract"* — never claiming input/output direction the graph doesn't
assert (`stops-series-full` cites both the M12 *and* M13 contracts, so
even the direction "produced by" vs. "primary subject of" isn't uniform
across that one predicate). This is a genuine, worth-fixing-later gap in
the `mc:` vocabulary (a `producesDataset` predicate would resolve it) —
noted as a recommendation below, not silently patched over in the UI.

## 7. Realizations, and the two-realizations comparison

**What a realization resource actually is** (verified, and worth being
precise about because it's slightly different from what doc 12 §2
implies): the `mc:Realization` resource itself carries almost nothing —
`mc:engine` ("DuckDB SQL") and a `rdfs:comment`. Its own comment says so
outright: *"The code text stays in the pattern; this resource is its
identity, not its copy."* The actual SQL lives in the linked
`rc:Pattern` resource's `rc:patternText` (reachable via the realization's
own `rdfs:seeAlso`), which `describe_pattern()` already returns cleanly
via the wheel. So a realization card is:

- Engine + label (e.g. "M12 realization: DuckDB SQL, version 2 (session
  13)") + the realization's own comment, which is usually where the
  *interesting* facts live (M12: "windowed one-pass DuckDB SQL... 427,134
  stop events from 92,454,453 broadcasts in 21.5 s. Version 2: version 1
  violated the silence-termination invariant and was replaced within
  session 13.").
- A `<details><summary>View the SQL</summary>...</details>` disclosure
  (native HTML, no JS needed — matches the project's existing CSS-only
  interaction idiom, e.g. the map/table view toggle) pulling the linked
  pattern's `patternText` verbatim into a `<pre>` block. Collapsed by
  default: per §1, SQL is not what leads.
- Linked run evidence (`rdfs:seeAlso` targets typed `rc:Evidence`),
  rendered with the same excerpt-and-link treatment as parameter
  evidence (§5) — this is where the concrete run stats live (row counts,
  timings) when they exist.

**Two realizations, side by side** (doc 13 §4 open question 2): no
contract in the live capsule has two realizations recorded today — v1 of
M12's realization was replaced in place, not kept as a second linked
resource, even though its existence is recorded in prose on the surviving
v2's own comment. So this part of the design is necessarily forward-
looking; flagged as such rather than pretended to be verified.

Design: when a contract's `hasRealization` list has more than one
member, render the realization cards in a **side-by-side grid** (CSS
grid, one column per realization, same row order within each column:
engine/label → comment → evidence → SQL disclosure) instead of the
default single stacked card. Because nothing in the `mc:` vocabulary
records a structured, comparable metric per realization (no
`mc:eventCount` or similar — everything numeric lives in free-text
comments and linked evidence summaries), do **not** attempt an automated
numeric diff. The value of the side-by-side layout is putting both
realizations' full context in the same eyeful for a human to compare by
reading, the same way the M12 v1→v2 story above is currently only
readable as prose. If a future realization pair *does* carry comparable
structured evidence (e.g. two `rc:Evidence` resources both reporting an
event count), a simple "Δ" line between the two summary numbers would be
a natural v2 addition — not built now because there is no real instance
to build or test it against.

## 8. Failure modes

Reuse `dataset.html`'s existing `caveat_card` macro verbatim (severity-
colored left border: severe/moderate/minor, using the same
`--severe`/`--moderate`/`--minor` CSS variables already in
`style.css`) rather than inventing new caveat styling. The macro expects
`{iri, label, description, impact, severity: {label}}` — since
`mc:hasFailureMode` targets are fetched by raw traversal (no wheel call
assembles this shape for `mc:`-linked caveats the way `describe_dataset()`
does for dataset-linked ones), the `workbench/methods.py` helper (§9)
must assemble caveats into that exact shape so the macro is a straight
import, not a reimplementation.

**Cross-method caveat reuse**: several caveats are cited by more than one
contract (verified: `ais-sentinel-values` and
`sentinel-encoding-shift-2025` by both M11 and M12; `m3-silence-is-not-
dark` and `missing-day-2024-08-26` by both M12 and M13). Add a small
"Also affects: M11, M13 →" line under a shared caveat's card — cheap
(one join over `mc:hasFailureMode` per caveat IRI, computed once across
all three contracts) and genuinely useful: if an analyst already knows
about a caveat from reading M12's page, seeing "this also affects M13"
tells them their existing mental model transfers, without re-reading the
caveat in full a second time.

## 9. Dependencies

Two lists, both from `mc:dependsOnMethod`:

- **Depends on** (this contract's own `dependsOnMethod` target — a
  `rc:Pattern` IRI, not necessarily a contract).
- **Depended on by** (reverse lookup: which contracts' `dependsOnMethod`
  points at *this* contract's own `forMethod` pattern).

For each target pattern, resolve whether it has its own contract (reverse
`mc:forMethod` lookup, same shape as the parameter-ownership lookup in
§4) and render accordingly: if it does, a card with the target's own
summary/label and a link straight to that contract page (e.g., from
M13's page, "depends on: M12 — per-vessel event-level stops series →");
if it doesn't (M11 depends on M7's dwell-span pattern, which has no
`mc:MethodContract`), render "no contract recorded for this method —
L0-only" with a link to the plain pattern resource page. Doc 12 §2 calls
L0-only methods "the smell that marks future L1 candidates" — say that,
don't hide it.

**A verified anomaly to design for, not around**: `M12`'s
`dependsOnMethod` resolves to the pattern behind **M11's own contract**
(`https://richcanopy.org/doxabase/generated/pattern/2fb8d9b7-...`) — even
though M12's own prose (§3, its full `PURPOSE`/`BEHAVIOUR` text) never
mentions M11 and reads as built directly from `broadcasts`. This is
almost certainly a mis-wired edge from when the contracts were authored,
not a real data dependency. The page's job under this design is to
render it exactly as recorded — a plain "depends on: M11 — physical
berth-vs-anchor discriminator →" card, honestly labelled, no attempt to
detect or "correct" the apparent mismatch. This is precisely the kind of
thing a human trust decision is for: the page's honesty here is what
lets a human catch it (as this design pass just did), not the workbench's
job to silently launder it into something that looks consistent (§1's
third bullet, this is its concrete instance).

## 10. Navigation in and out

- **Global nav** (`base.html`): add a `Methods` link next to `Datasets` /
  `Types` / `Revisions`.
- **`/methods` index**: one row per `mc:MethodContract`
  (`list_entities(type='https://ais.study/mc#MethodContract')` already
  works unmodified against the project-local IRI — no wheel change
  needed), leading with the same stat-pill counts as the detail page's
  header (invariants / parameters / realizations / failure modes) so an
  analyst can triage which method to open first, the same "lead with the
  number that makes it tractable" principle `/datasets` already applies
  to row counts.
- **From a dataset page → its method**: dataset pages already render
  `rdfs:seeAlso` links generically (any `seeAlso` target shows as an
  outgoing triple row today); worth a small, explicit addition —
  `dataset.html` grows an "Analytical methods" line right under the
  header pills when any of a dataset's `seeAlso` targets is typed
  `mc:MethodContract`, using `method_url()` instead of the generic
  `resource_url()` so it routes to the new structured page instead of the
  flat one.
- **From a method page → its consumed/related datasets**: `dataset_url()`
  throughout (§6), same helper the rest of the app already uses.
- **From a method page → neighbouring methods**: `method_url()` for
  dependency links (§9); falls back to `resource_url()` for L0-only
  dependency targets that have no contract.
- **From a caveat's own resource page → the methods it affects**: no new
  code — `resource.html`'s existing generic incoming-triples table
  already lists every `mc:hasFailureMode` triple pointing at a caveat
  (verified: `mc:hasFailureMode` has a proper `rdfs:label`, "has failure
  mode", so it renders cleanly today with zero changes) — landing on
  `caveat/timestamp-cet-parse-bug`'s own page already shows "M12 contract
  — has failure mode" as an incoming row. This is free; just noting it so
  no one duplicates it as new work.

## 11. What is deliberately omitted, and why

- **No live invariant-check execution.** Running the invariants against
  the frames they describe (turning L1 promises into pass/fail) is a
  real, valuable future feature — but it's a compute feature (needs a
  query engine against potentially-large frames, a result cache, staged
  re-runs), not a rendering feature, and doc 12 explicitly frames
  invariants as "future generated tests," present tense not yet. Building
  a fake status pill now would be worse than not having one (§1).
- **No automated realization diff.** See §7 — nothing in the data model
  gives two realizations comparable structured metrics yet; forcing a
  diff would mean inventing false precision (e.g. string-diffing SQL
  text, which measures nothing about behaviour).
- **No write path, no annotation, no "flag this parameter" affordance.**
  Doc 13 decision 1 is unambiguous (agents write, humans see) and
  explicitly calls out that a premature annotation feature "would create
  a second write path around the epistemic ladder." A method page is
  exactly the kind of page where an analyst will *want* to leave a note
  ("this ambiguous band looks wrong for tugs") — that impulse is real and
  correctly out of scope for v1; it belongs behind the same
  ephemeral-entities/review-lane design every other write path is
  waiting on, not a bespoke shortcut here.
- **No History section.** `resource.html`'s History section
  (`list_resource_revisions`) is IRI-generic and would technically work
  against a contract or parameter IRI with zero new code. It's left out
  of required scope anyway because every contract in the live capsule was
  authored in one revision each — a history timeline with exactly one
  entry adds a whole section of near-empty chrome for no orientation
  value today. Worth adding the moment a contract actually gets revised
  a second time (e.g. a parameter re-tuned after new evidence) — flagged
  as a natural, cheap v1.1, not a v1 requirement.
- **No `producesDataset` UI beyond the honest "related datasets" panel**
  (§6) — the vocabulary gap is real; papering over it in the UI would
  hide exactly the kind of thing doc 12's "couldn't-say list" is designed
  to surface. Recommended as an `mc:` vocabulary addition for whoever
  next touches doc 12, not fixed here.
- **No cross-domain generalization.** This design is read entirely off
  one project's `https://ais.study/mc#` terms. Doc 12 §4 is explicit that
  `mc:` stays project-local until a second domain independently needs the
  same terms — the workbench code should follow the same discipline the
  vocabulary does: no attempt to make this page generic over an
  as-yet-hypothetical second `mc:`-shaped project.

## 12. Implementation notes for whoever builds this

- **The wheel has zero `mc:` awareness** — verified by grepping
  `doxabase/core/` for `MethodContract`/`hasInvariant`/`Realization`:
  nothing. `describe_pattern()` is genuinely useful (structured
  `pattern_text`/`rationale`/`supporting_claims`/`evidence` with sources
  already resolved) for the Realizations section's SQL pull and for any
  L0-only dependency target, but the contract/invariant/parameter/
  realization/failure-mode graph itself needs a dedicated new module,
  `workbench/methods.py`, following the exact idiom `dataset_index.py`
  and `graph_types.py` already established for "project-specific rollup
  the wheel doesn't cover, direct SQL over `quads`, cheap and fast."
- **Performance**: a full contract assembly (M12: 1 contract + 7
  parameters + 5 invariants + 5 caveats + 1 realization + assorted
  evidence/claim hops for parameters that cite them) is on the order of
  25-35 individual resource lookups if built naively as one
  `describe_resource()` call per node — each measured at ~1ms against
  this capsule elsewhere in the app, so probably fine, but tight against
  doc 13's <100ms floor once evidence excerpts are included. Recommend
  `methods.py` do this as a handful of batched SQL queries (one for all
  `hasParameter`/`hasInvariant`/`hasRealization`/`hasFailureMode` edges
  from all three contracts at once, joined against a batched label
  lookup) rather than N sequential Python-level `describe_resource()`
  calls, the same batching `graph_types.py` already does for `/types`.
- **Plot serving**: see §5 — reuse `frames._data_root()`'s root-resolution
  and containment-check pattern; don't invent a second one.
- **`caveat_card` macro reuse**: see §8 — assemble the failure-mode shape
  to match, import the macro, don't refork it.

## 13. Acceptance checks

Concrete, runnable against the real capsule
(`/home/codex/ais-study/capsule.sqlite`), each targeting a specific,
verified fact from this research pass rather than a generic smoke test:

1. **Plots actually render.** `GET /method?iri=https://ais.study/contract/m11-berth-anchor-discriminator`
   must contain an `<img>` tag whose `src` is (or resolves through)
   `/evidence/plot?path=work/plots/m11_a_radius_mean_hist.png` (or one of
   its four siblings), and a direct `GET` on that `/evidence/plot` URL
   must return HTTP 200 with `Content-Type: image/png` — not just a text
   citation of the path. This is the one feature doc 13 names by name;
   if it doesn't render an actual image, the page hasn't met the brief.
2. **Structural completeness, M12.** The M12 page shows exactly 5
   invariant cards, 7 parameter cards, 1 realization (single-column, no
   comparison chrome — there's only one), and 5 failure-mode caveat cards
   with correct severity coloring (`timestamp-cet-parse-bug` renders with
   the "severe" red-bordered treatment, `m13-shoulder-undercounting`-style
   caveats would render "minor" green — confirm at least one severe and
   one non-severe caveat render with visibly different styling on the
   same page, since M12's own 5 failure modes span more than one
   severity).
3. **Cross-method parameter reuse is visible, not hidden.** The M13 page's
   `m13-movement-symmetry` invariant shows a "constrained by" entry for
   `m12-silence-gap` labelled as belonging to the M12 contract (e.g.
   containing the text "M12" and linking to
   `/method?iri=https://ais.study/contract/m12-stops-series`), visibly
   distinct from the four parameter cards that belong to M13 itself.
4. **The M12→M11 dependency renders honestly.** The M12 page's
   Dependencies section shows a "depends on" entry resolving to
   `https://richcanopy.org/doxabase/generated/pattern/2fb8d9b7-...` (M11's
   pattern) with a link into the M11 contract page — present and
   unmodified, even though nothing in M12's own rendered purpose/behaviour
   text (item 2 on the same page) mentions M11. The test is explicitly
   that the page does *not* suppress, "correct," or omit this edge.
5. **M13's outputs don't fabricate a link that isn't there.** The M13
   page's Output section shows the `outputGrain`/`outputMeaning` prose
   naming `feed_outages` and `stop_boundary_reasons`; its "Related
   datasets" panel contains `stops-series-full` (found via a real
   incoming `rdfs:seeAlso` edge) but does **not** contain
   `https://ais.study/dataset/feed-outages` or
   `https://ais.study/dataset/stop-boundary-reasons` as clickable
   graph-derived links, since no edge connects them to the contract today
   — confirming the page reports the real graph shape rather than
   inferring a link from the prose match on frame names.
