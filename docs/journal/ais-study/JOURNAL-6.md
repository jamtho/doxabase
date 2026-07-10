# JOURNAL-6 — Session 6: Two Stories, Built to Last

## Orientation

Read BRIEF-6.md, bridge.py, query.py. Ran `bridge.py tools` -> tools6.json (24
tools). Oriented via project_brief, get_doc (start_here, graph_roles,
working_the_capsule, observation_recording, patterns, map_authoring,
ontology_primer, analysis_packets, staged_revisions, systematisation),
graph_overview.

Key discovery: the capsule already has a project vocabulary `https://ais.study/ns#`
(aisv:) — 7 classes (AisIdentity, IdentityChange, Emitter, SilencePeriod,
DwellPeriod, CargoOperation, OperationalTie) and 18 properties, distilled by
session 5 from the 20 existing vessel-story patterns + method patterns +
caveats + expert observations (staged-revision 1cb51827, applied 63a8dbb1).
Session 5 then proved the vocabulary out on 3 existing stories (311050400,
367369920, 538002783), re-expressing them as `aisv:` resources in `map`. The
**first** attempt at that (staged-revision 82e62837, patch using
`rc:supportingClaim`/`rc:summary` on the aisv: resources) failed SHACL
validation (41 violations) because `rc:supportingClaim` binds the subject to
the full `rc:PatternShape` contract regardless of the resource's own
`rdf:type`. The **repaired** version (staged-revision cca8ed52, applied
82dcb85b) uses `rdfs:seeAlso` to cite claims and `rdfs:comment` for narrative
instead — that is the convention I will follow. Recorded as a friction
finding in the repair's rationale; I inherit the lesson rather than
rediscovering it the hard way.

Controlled literal values (documented, not SHACL-closed, but I will stay
inside them) fetched via describe_resource on each property:
- `changeMechanism`: rename_same_hull, spelling_variant, mmsi_reassignment,
  statics_correction, slot_handover_shared_mmsi, collision_relabel, unresolved
- `hullContinuityBasis`: imo_callsign_persist, dims_and_operating_continuity,
  draft_continuity, position_stream_continuity, none_multi_emitter
- `datingQuality`: dated, windowed, year_only_undatable
- `emitterMultiplicity`: single, position_jitter, multi_emitter,
  placeholder_shared, unresolved
- `emitterKind`: vessel, fixed_installation, gear_beacon, aircraft
- `silenceReading`: in_place_power_down, coverage_exit_voyage, gear_recovered,
  unexplained, implausible_jump
- `dwellKind`: port_call, lay_up, refit, worksite_deployment, berth_stay,
  anchorage_wait
- `cargoDirection`: loading, discharge, ambiguous_ballast
- `tieKind`: project_fleet_sisters, towed_work_spread, company_tug_pair

Existing corpus already covers 20 storied vessels (pattern/vessel-*):
111227501, 303520000, 311050400, 316001262, 338024391, 360000000, 366971370,
366991421, 367369920, 367373000, 367677560, 368166560, 368574000, 369305000,
369914086, 538002783, 941217116, 999999999, plus two `generated/*` patterns
(367615990, 338617000). Confirmed via `list_entities` + reading the pattern
list in full. Only 3 of these (311050400, 367369920, 538002783) have the
richer `aisv:` structured form; the rest are pattern-only prose.

Caveats catalogued (24 total) — IRIs noted for citation. Method patterns
M1-M5 have recorded query snippets (`ais.study/query/m1..m5-*`) I can run
verbatim through query.py. There is also an M6 (port/terminal visit
detection) as an informal pattern, not yet a formal analysis_view — not
needed for this session.

## Candidate search (index-layer only, per budget discipline)

Ran M1 SQL verbatim (year-boundary identity classifier) against
`s3://ais-noaa/index/*/*.parquet`. Full classification: 1,288
rename_same_hull, 977 ambiguous_name_change, 754 name_present_one_year_only,
301 spelling_variant_same_hull, 169 suspected_mmsi_reassignment.

Picked **MMSI 374158000** (LOTTUS 2024 -> EVER FOCUS 2025) for the
identity-complicated slot. It already appears in the capsule as an "M1
worked example" (observation e367f6ae / claim 0ab2a720), asserted there as a
plain "different physical vessels" reassignment — but it was never made into
a full vessel story (no `pattern/vessel-374158000`, no AisIdentity node), so
it is fair game per the brief's search-verified test. My own broadcast-level
follow-up found something that worked example didn't check: (a) the
dominant occupant (~74% of active days, both years) sits at the exact same
stationary position, 33.762N/-118.183W off Long Beach CA — continuity the
"different vessels" framing doesn't address; (b) M2 flags this MMSI as an
extreme multi-emitter case (conflict_days 175/723, median conflict-day span
33.1 deg — wider than the already-storied 367369920's 2.83 deg); broadcast
spot-checks on 3 separate conflict days (2024-01-25, 2025-03-16/17) show
the SAME complete identity (name+IMO+call sign) broadcasting simultaneously,
stationary, from a *different* US location each time (Boston MA; coastal
Georgia) — not GPS jitter (I first suspected that from the location-bin
scatter, then ruled it out by reading raw broadcast rows: each "conflict"
site is itself internally stationary and coherent for the whole day, not
noisy single-point jumps). Net read: one dominant, physically continuous
occupant whose displayed identity was corrected (not reassigned) at the
year boundary, PLUS a real multi-emitter phenomenon (other stationary
transmitters elsewhere intermittently broadcasting the identical borrowed
identity) that the existing claim's "different physical vessels" framing
missed entirely. Full detail + numbers in the claims recorded below.

Picked **MMSI 368817000 (COMFORT)** for the operationally-interesting slot.
Type 58 (medical transport) turned up only 11 MMSIs feed-wide; COMFORT
(273 m, IMO7390478, call sign NCOM) and its near-neighbor 367816000 (MERCY,
IMO7390454) stood out immediately as US Navy hospital ships (real-world
identification, not feed-derived — flagged as such in the record). COMFORT
has excellent coverage (586 active days across 2 years) vs MERCY's 22 days
in 2024 only, so COMFORT is the workable one. Ran M3 (silence-gap SQL)
against this MMSI directly: clean signal — 3 `silent_in_place` gaps (25d,
13d, 36d) all at the same Gulf-coast berth (30.68N/-88.03W), one messy
pair (`local_gap` 64d + `coverage_exit_voyage` 2d, 2025-06-08 -> 2025-08-16)
that is really ONE ~68-day absence split into two by a single intervening
position ping near Puerto Rico — M3's per-gap displacement rule can't see
that. This is itself a fresh, evidenced methodological finding about M3
(distinct from the already-recorded m3-coverage-geometry-blind caveat, which
is about *under-calling*; this is a splitting artifact from an isolated
mid-voyage fix). Neither vessel is cargo-cycling (draft irrelevant to a
hospital ship) so this is squarely the "seasonal pattern / non-ship
curiosity" lane, not a rehash of the two already-storied tanker cases.

## Recording plan

Both vessels get: rc:Claim(s) with query-result evidence citing
`s3://ais-noaa/index/*/*.parquet` (and the broadcasts glob for spot-checks),
an rc:Pattern synthesis (`pattern/vessel-<mmsi>`), then a hand-authored TriG
patch to `map` via `stage_revision(kind="graph")` using the *repaired*
convention (rdfs:seeAlso + rdfs:comment, not rc:supportingClaim/rc:summary),
dry-run check, apply, then `validate_graph(scope="all")`.

374158000: AisIdentity + one Emitter (the Long Beach dominant occupant —
I did NOT attempt full per-message segregation of the secondary sites, so I
am not minting Emitter resources for those; recorded as a couldn't-say) +
one IdentityChange (statics_correction / position_stream_continuity, for the
dominant occupant) + a claim_reconsideration (relation "refines") on the
existing worked-example claim 0ab2a720.

368817000: AisIdentity + one DwellPeriod (berth_stay, 2025-02-05..05-06,
exactly bounded by zero-movement days either side) + 3 SilencePeriod
resources (2 clean in_place_power_down winter gaps + 1 coverage_exit_voyage
spanning the split Caribbean deployment, cross-linked via rdfs:seeAlso and
commented to explain the M3 splitting artifact).

Continued below as work proceeds.

## Recording — done

Recorded, in order:
- `record_observation(kind=claim)` x2 for 374158000: `claim/374158000-identity-and-persistence`,
  `claim/374158000-multi-site-emitters`.
- `record_claim_reconsideration` (relation `refines`) linking the new
  identity-and-persistence claim to the existing M1 worked-example claim
  `generated/claim/0ab2a720...` — reconsideration IRI
  `generated/claim-reconsideration/86605069-1339-4af2-a507-6d48fc86ed36`.
- `record_pattern`: `pattern/vessel-374158000`.
- `record_observation(kind=claim)` x3 for 368817000: `claim/368817000-identity-and-mobility`,
  `claim/368817000-gulf-berth-pattern`, `claim/368817000-2025-deployment-split-gap`.
- `record_pattern`: `pattern/vessel-368817000`.
- `stage_revision(kind="graph")` with a hand-authored TriG patch (36
  resources' worth of statements, 72 triples) adding, to `map`:
  - 374158000: `AisIdentity`, one `Emitter` (dominant occupant only —
    deliberately did not mint an Emitter for the secondary sites; see
    couldn't-say below), one `IdentityChange`.
  - 368817000: `AisIdentity`, one `DwellPeriod`, three `SilencePeriod`
    (two clean in-place gaps + one deliberately-merged coverage-exit
    silence spanning what M3 reports as two adjacent gap rows).
  - Every resource links its supporting claim(s) via `rdfs:seeAlso` and
    carries narrative in `rdfs:comment` — the *repaired* convention
    (session 5's first attempt at this exact move, staged-revision
    82e62837, used `rc:supportingClaim`/`rc:summary` on these same
    non-kernel classes and failed 41 SHACL checks because those predicates
    bind the subject to the full `rc:PatternShape` contract regardless of
    `rdf:type`; the fix, staged-revision cca8ed52, is the one I copied).
  - Staged validation preview: `validation_conforms: true`, 0 results.
  - `apply_staged_revision(dry_run=true)`: `status: ready`, `can_apply: true`.
  - Applied: `applied-revision/a6aa2a1f-3263-4fd8-87e4-977a17d0a026`,
    72 triples added, `validation_conforms: true`.
  - Post-apply warning flagged staged-revision `82e62837` (session 5's
    already-superseded first attempt) as a "stale sibling" merely because
    it also touched `map`. Checked `plan_staged_revision_recovery
    (current_staged_work_only=true)`: **0 rows** — it is not live staged
    work (already closed out with a `review_decision: superseded` in
    session 5), so nothing was orphaned by my apply.
- Final `validate_graph(scope="all")`: **conforms: true, result_count: 0**.
- `project_brief` key_counts before/after: observations 72->77 (+5),
  claims 58->63 (+5), patterns 32->34 (+2), evidence 80->85 (+5),
  graph_revisions 6->8 (+2), graph_patches 3->4 (+1), graph_snapshots 8->10
  (+2) — matches exactly what I recorded, nothing extra, nothing missing.
- `list_entities(type=AisIdentity, graph=map)`: now 5 (the 3 from session 5
  plus `mmsi-374158000` and `mmsi-368817000`).

## Couldn't-say list (this session's additions)

1. **Un-segregated secondary emitters (374158000).** The vocabulary's
   `Emitter` class is for a *confidently separated* physical track (the
   expert's movement-continuity segregation, observation a79e1c6e — "proven;
   expensive"). I only spot-checked 3 conflict days at the broadcast level;
   I did not run full per-message segregation across 2 years. I therefore
   minted an `Emitter` for the dominant Long Beach occupant only, and left
   the secondary sites as a described phenomenon (`emitterMultiplicity
   multi_emitter` + prose in `rdfs:comment` + claim
   `374158000-multi-site-emitters`) rather than inventing a second Emitter
   resource I could not fully justify. There is no vocabulary term for
   "an unknown, unlocalized number of secondary emitters" short of the
   existing `emitterMultiplicity` value `unresolved` — I used `multi_emitter`
   instead since at least one secondary emitter (per spot check) is
   confidently *not* jitter, but the count and full location set genuinely
   are unresolved. A future session with budget for full segregation could
   upgrade this.
2. **One mechanism per IdentityChange, but this MMSI has two.** The
   dominant occupant's year-boundary change (statics_correction) and the
   MMSI's overall multi-emitter nature are two different, both-true
   readings that the single-valued `aisv:changeMechanism` /
   `aisv:hullContinuityBasis` pair cannot hold at once. I resolved this by
   scoping the `IdentityChange` resource's `rdfs:comment` explicitly to
   "the dominant occupant only" and keeping the multi-emitter reading on a
   separate property (`emitterMultiplicity`) of the parent `AisIdentity`.
   This works, but it is a modelling seam: nothing in the graph *forces*
   a reader to notice the IdentityChange's mechanism doesn't cover the
   whole identity — only the prose says so.
3. **Merged SilencePeriod, mechanically two M3 rows (368817000).** No
   `aisv:` term exists for "this SilencePeriod is a reviewed merge of two
   raw M3 gap rows connected by one intervening low-signal fix." I
   recorded ONE `SilencePeriod` spanning the full window with the merge
   explained in `rdfs:comment` and the full mechanical detail (both raw
   M3 rows, exact dates/displacements) preserved in the backing claim
   (`368817000-2025-deployment-split-gap`) rather than the graph resource
   itself. A future vocabulary revision could add something like
   `aisv:mergesGap` (a list of raw method-output identifiers) if this
   pattern recurs.
4. **No place for "background/world-knowledge identification, not
   feed-derived."** I identified COMFORT as a US Navy hospital ship by
   general/world knowledge, not from the feed (which only gives name,
   IMO, call sign, type=58, length). I kept this out of the graph
   resources entirely (no aisv: resource asserts "hospital ship" or
   "US Navy") and confined it to one flagged sentence in the backing
   claim's prose. The existing `rc:SourceKind` controlled vocabulary has
   no "world knowledge / background, not verified against this dataset"
   value — every `rc:sourceKind` option assumes the claim is grounded in
   *some* project-visible source. This is the same gap the ontology
   primer implicitly warns about (self-reported, unverified identity
   fields) but one level further out: not just "the feed's identity claim
   is unverified" but "my identification of what the feed's identity claim
   *refers to in the real world* is unverified and inherently outside the
   feed."
5. **No Voyage/excursion class** (already flagged by session 5's
   couldn't-say list, independently rediscovered here for COMFORT's 2025
   Caribbean trip and 374158000's status as an anchored/laid-up hull) —
   both would have been better served by a bounded "voyage" resource with
   its own start/end/waypoints than by stretching `SilencePeriod` (a
   *silence*, not a positive record of the voyage itself) to carry that
   meaning. I used `SilencePeriod` because it is the closest fit the
   vocabulary offers, not because it is the right shape.

## Friction notes

- The bridge's error messages for malformed tool args are decent but the
  `stage_revision(kind="graph")` `additions` dict shape (`{"graph":...,
  "content":...}`) is not spelled out character-for-character anywhere in
  `mcp_tools` — I inferred it from the `systematisation` doc's
  `graph`+`content` shorthand description and from reading an *already
  applied* graph-patch's stored Turtle via `describe_revision`/`search`,
  not from a doc that names the `stage_revision(kind="graph")` field shape
  directly. It happened to be right first try, but that was inference
  from precedent, not documentation.
- `bridge.py call <tool> '<json>'` genuinely cannot take a JSON value
  as a bash argument once it's over a few hundred characters or contains
  apostrophes (vessel names like TALUS's, curly quotes, etc.); every
  non-trivial call in this session went through `@scratchfile.json`, per
  the brief's own advice — that advice is correct and necessary, not
  optional, for claim_text/rationale fields of the length this work
  needed.
- Discovering the "already-storied" set required reconstructing it from
  the `pattern` graph's `rc:Pattern` `list_entities` output (32 patterns,
  20 of them `vessel-*`), *not* from `project_brief`, which does not
  surface a "which vessels are already storied" queue. A `project_brief`
  or dedicated helper that answers "list storied vessel MMSIs" directly
  would have saved a few calls.
- The post-apply "stale sibling" recheck warning fired for a revision
  (82e62837) that was already fully closed out (review_decision:
  superseded) in a prior session; `plan_staged_revision_recovery` correctly
  filtered it back out to zero, but a first-time reader could easily
  mistake the raw post-apply warning for a new problem they introduced.
  Worth knowing: always follow up a "sibling went stale" warning with the
  recovery planner, not just re-reading the sibling's old validation
  errors — the two things are unrelated here.

