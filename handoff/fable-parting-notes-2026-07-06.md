# Parting Notes — Fable, 2026-07-06

Written on the last full day of Fable availability, at James's request:
"whatever you think could be useful" for the models that carry on. The
project state is in `handoff/distillation-session-2026-07-04.md`,
`docs/journal/waves.md`, and design docs 06–10; this document is
everything *else* — judgement, traps, and method that I'd otherwise take
with me. It is long on purpose. Read the state documents first; read this
before doing anything hard.

## STATE AT HANDOVER (updated 2026-07-07 night)

**Fable access extended ~5 days (to ~2026-07-12)**, so this is a living
frontier again, not a last word. James's review is running as an active
conversation: **expert round 2** (VOCAB-NOTE feedback + four addenda) is
digested in `/home/codex/ais-study/expert-feedback-round-2.md` and
recorded as nine capsule observations. Its yields so far: the
vocabulary-v2 ledger (layer-1 facts vs layer-2 inferences, naming
humility for CargoOperation/OperationalTie, indexical assessment
windows, candidate/declared identity split with non-AIS anchors as the
declaration threshold, the state-vs-ephemera architecture: populations
in frames, methods+exemplars in graph); tradecraft (gear beacons
broadcasting battery in COG, fine-grained histogram-shape study, SOG
bimodality for data-derived thresholds); and two commissioned sessions —
7 (M7/M8 track context, layering confirmed quantitatively), 8 (M9
shuttle census: 820 shuttles), and 9 (all 17 stopped shuttles verified
vessel-side — the honest negative; M10 stop-verification checklist
recorded; economic-indicator thesis calibrated, its real test needs the
~18 further years of data). Foursquare open places is the candidate
reference dataset James may load to S3 — pilot target: the flagged
endpoints from sessions 8/9. Everything is
committed and pushed to `master`; the gate is green; nothing is
half-done. The frontier:

- **Waiting on James** (in order): his audit of the six AIS session
  reports in `/home/codex/doxabase-reports/` (findings become distiller
  batch 2, run per `docs/journal/distiller-pass-1.md`'s template); the
  `rc:citesClaim` decision (§6); report shareability sign-off (all
  reports are local-only pending his review); the wave-22 schema
  end-state signature in waves.md if still unsigned.
- **Open distiller-batch-2 ledger** beyond his audit: M-method upgrade
  gaps (session-4 trial record), vocabulary-v2 couldn't-say evidence
  (session 5 + 6 trial records — Voyage class leads), review-reason
  wording items already resolved; check trial records' product-findings
  sections for anything marked unfixed.
- **His pipeline reminders** (memory `james-followups`): CET timestamp
  bug, missing day 2024-08-26, source CSVs for the freeze question,
  index-metric precompute ideas. Surface when he touches ais-noaa-fetch.
- The study capsule (`/home/codex/ais-study/capsule.sqlite`) validates
  clean, no orphaned staged rows; its venv wheel is current.

---

## 1. The one lesson above all others

This project nearly died of additive optimization. Every individual
change in the old loop was locally reasonable; the system they summed to
was unusable. The cure was not better taste — it was **instruments plus
subtraction**: a scoreboard whose ceilings only move down, a gate that
blocks regressions mechanically, and the discipline of recording
observations widely but acting on them rarely, in batches, with
simplicity as the distiller's explicit brief.

You will feel the pull constantly. Every trial surfaces friction; every
friction suggests an addition; every addition is locally justified.
The rules in `AGENTS.md` are not bureaucracy — they are the memory of a
74,000-line file. When an agent gets lost, the allowed fixes are, in
order: better state presentation in an existing field; a rewritten doc
sentence; a merged response. Re-read doc 06's "root cause" section
whenever a new response field seems obviously necessary. It always seems
obviously necessary.

The corollary that took me longest to internalize: **deletion needs as
much precision as creation**. Every deletion wave here (fields, tools,
docs) was specified as exactly as an implementation — what dies, what
absorbs it, what carries the semantics forward. "Remove the old stuff" is
not a spec.

## 2. How to run the sub-agent economy on this project

Most of the heavy work here was done by sub-agents, and the difference
between their good and bad runs was almost entirely in the briefs:

- **Enumerate the traps.** The R3 staging agent succeeded on an 18-tool
  merge because its brief listed the exact failure modes R1 discovered
  (string-based `add_action` helpers, `find_exact_action` matchers,
  repair-hint `arguments_template` dicts, effect-classification tables).
  A capable model with a vague brief re-discovers traps expensively; a
  capable model with an enumerated trap list is surgical.
- **Give verification criteria, not vibes.** Every good brief ended with:
  exact suite counts expected, the gate commands, "explain any delta",
  "do NOT commit". Agents rise to checkable standards.
- **The implement/reconcile split works.** Change product code yourself
  (or with a strong agent), then hand test reconciliation to a cheaper
  agent under the rule "rename keys, delete assertions on removed fields,
  NEVER weaken which-tool/which-args/which-value semantics". This split
  was used five times; it never produced a bad merge.
- **Do not batch-regex test files.** I did this once (waves.md wave 11
  records it); it over-matched, broke ten more tests than it fixed, and a
  Sonnet agent's per-site edits had to clean up after me. Tests encode
  semantics; edit them at semantic granularity.
- **Never edit files an active agent owns.** When I slipped (a one-block
  emitter edit during the module-split run), the agent handled it — it
  verified its own diff in an isolated git worktree, which is a trick
  worth copying — but the risk was mine, not its.
- **Resumption works.** Agents cut off by quota limits resume from
  transcript with `SendMessage`, their working tree intact. Do not
  panic-revert a half-finished agent tree; check `git status`, read what
  it said last, resume it.
- **Read error counts skeptically.** An agent reporting "6 errors" may
  mean 6 deliberate discovery probes (T2's empty-spec calls against
  kind-dispatched tools are the intended path). Accidental vs intentional
  errors are different metrics; the trial reports distinguish them.

## 3. Codebase traps, in the order they will bite you

1. **The facade injection loop** (`doxabase/core/__init__.py`, bottom).
   Mixin methods that reference `DoxaBase` at runtime work because the
   composed class is injected into every mixin module's globals after
   composition. A new core module must be added to BOTH the class bases
   and the injection tuple. This is transitional; rewriting call sites to
   `type(self)`/`cls` and deleting the loop is welcome cleanup.
2. **`doxabase_internal` field metadata** (`_shared.to_jsonable`): fields
   marked with it exist for Python callers but never serialize to MCP.
   This is the standing mechanism for "keep the capability, shed the wire
   cost". Check for it before assuming a field is dead.
3. **Kind/spec dispatch** (`mcp_tools._dispatch_kind`,
   `_merge_spec_into_call`): validation errors that name the valid and
   missing fields per kind are **load-bearing product surface** — the
   trials proved agents self-correct from them in one step. They are
   tested behaviorally. Never replace a targeted error with a generic one.
4. **The generated tool doc**: `docs/agent/mcp-tools.md` is generated by
   `tools/gen_docs.py`; `tests/test_gen_docs.py` fails the gate on drift.
   Any tool-signature change requires regeneration. One known soft spot:
   the generator's `FLAT_REQUIRED` map mirrors a few inline-enforced
   required fields by hand — the one place doc drift is possible without
   a code-table change.
5. **Renaming or merging a tool ripples further than you think.** The
   full checklist, learned across five waves: server registration;
   `mcp_tools` function; core suggestion emitters (constructor calls AND
   args-dict templates AND string-based `add_action` helpers AND
   `find_exact_action`-style matchers AND repair-hint
   `arguments_template` dicts AND prose in error messages/reasons);
   effect classification in `_shared.py`; tests that re-dispatch
   suggestion args into Python methods (they must unwrap `spec`);
   examples; the generated doc. Grep for the quoted `"doxabase.<name>"`
   string and expect ~10 distinct usage shapes.
5b. **Trial environments pin their wheel.** Study venvs (`ais-study`,
   the Enron study) install the wheel current at setup time; a product
   fix does not reach them until you rebuild + reinstall. Session 3 hit a
   "bug" that was actually wave-25's fix, undeployed. After any product
   fix that a running study depends on: `uv build` and reinstall into the
   study venv, and re-verify through the study's own bridge.
6. **The wave-23 lesson, twice-paid**: adding parameters to a core method
   is not a feature until the MCP tool wrapper exposes them and the doc
   is regenerated. The first real field session found exactly this gap
   (caveat evidence params, claim identity IRIs). When you touch a core
   signature, walk it out to the wire.
7. **MCP door vs Python facade divergence is intentional.** The Python
   API keeps `check_staged_revision_apply`, `draft_query_plan`,
   `export_kind=` etc.; the MCP doors fold them into `dry_run` /
   `plan_candidate` / `kind`. Docs must say which surface they describe;
   "Python API note" blocks are the established form.
8. **Budgets**: ceilings live only in `tools/scoreboard.py` and only move
   down. End-states change only via James, through the proposal valve in
   `AGENTS.md` (argue in the journal, never bundle with the change). The
   schema-chars end-state is 31,000 by his explicit sign-off (wave 22).

## 4. The trial methodology (use it; don't reinvent it)

The bridge pattern (`scratchpad battery dirs`, or `/home/codex/ais-study/
bridge.py`): dispatch through `build_server().call_tool` so payloads are
byte-identical to MCP, log per-call char counts, charge the full
tool-registry JSON as a session constant. Cold agents, one per task,
forbidden the repo. Costs are `chars ÷ 4`. Baselines and reruns must be
like-for-like: same tasks, same rubric, same agent class (Sonnet is the
standard trial agent — deliberately, as the representative consumer).

The probes that produced the best signal, reusable anywhere:
- **Blind answer key**: the grader writes down what they know before the
  agent runs; grade the capsule against it afterwards.
- **Deliberately untaught gap**: know a technique, don't teach it, watch
  whether it emerges (James's low-SOG dwell method is the live example).
- **Retrieval-vs-rederivation**: set a task whose answer is already
  recorded; watch whether the agent finds it or rebuilds it.
- **Wrong-hunch**: a breezy task on a capsule with a live gate; success
  is deliberate handling, not refusal or compliance.
- **Transfer economics**: strong model invents and records; weak model
  applies cold. This is the product thesis in miniature and the single
  most convincing demonstration we have.

All numbers to beat are in `docs/journal/trials/` — baseline, Gate-3,
Gates-5/6. If a change claims to help agents, the battery is how you
know.

## 5. Product convictions (mine, earned, held loosely)

- **State, not script, survived contact with reality.** The gates/queues
  brief carried four different cold agents through orientation, a
  recovery-gate dilemma, and a real inherited project. If an agent gets
  lost, the temptation to add a routing field will return; the fix has
  been better state presentation every single time so far.
- **The caveat/pattern layer is the product.** In the Enron study the
  handoff's review gates traced to recorded graph facts, not agent
  improvisation. In the AIS study the methods became patterns with
  executable views. When evaluating any change ask: does this make the
  capsule carry more of the weight, or the agent?
- **TriG-first is measured, not aesthetic**: the same graph content cost
  6.5× more as JSON triples. Don't let per-triple JSON shapes creep back
  into envelopes.
- **Targeted errors are cheaper than schema completeness.** The kind/spec
  trade works because a failed call costs one round trip and teaches the
  exact fields. Guard the error quality, not the schema size.
- **The report is an export artifact.** It carries the shareability
  banner and faithful-but-escaped literals because it inherits the
  privacy posture. Any future explorer app must inherit the same posture,
  not weaken it.
- **Docs rot is the fastest rot.** The docs were the biggest single cost
  in the Gate-3 battery — not the tools, the *stale docs about dead
  tools*. The generated-doc-plus-drift-test pattern is the antidote;
  extend it (worked examples should regenerate or die).

## 6. The AIS study — state and how to carry it

- Session 1 (strong model, cold, empty capsule): five methods recorded as
  pattern+caveats+view+evidence, three vessel stories, the "AIS lies"
  caveat catalog. Report: `docs/journal/trials/2026-07-ais-session-1.md`.
- Expert channel round 1: James's answers + volunteered tradecraft are IN
  the capsule (5 observations, refined identity-freeze caveat). The freeze
  was traced to the broadcasts layer by direct experiment — his index
  builder is exonerated; mechanism awaits source CSVs + provider PDFs.
- Session 2 (weak model, cold, capsule-only): the transfer proof.
  Applied session 1's methods by IRI, reproduced M5's numbers, invented
  M6 (low-SOG dwell — James later confirmed it as real tradecraft the
  strong model missed), and filed an evidence-backed counterexample
  against M1. Graded in `2026-07-ais-session-2.md`; human-facing version
  in `docs/worked-example.md`.
- Session 3 (curator): literature onboarding — provider PDFs + receiver
  gpkg reconciled against empirical caveats; identity-freeze traced
  further (probable mechanism: provider's AVIS/AVID correction DB).
- Session 4 (story corpus): fifteen vessel stories across the
  menagerie, recorded as observations/claims with evidence.
- Session 5 (vocabulary distillation): the ontology-pack experiment.
  25-term `aisv:` vocabulary (AisIdentity ≠ Emitter is the load-bearing
  insight), staged into the ontology graph via the full review loop,
  **zero data queries needed** — it ran entirely on recorded knowledge.
  It also exposed the review-decision minting bug (fixed same day,
  `e38a2e2`). The couldn't-say list in its trial record is the v2
  vocabulary roadmap (trade lanes, voyages, Place-as-resource).
- Session 6 (blind vocabulary-transfer probe, 2026-07-07): a cold weak
  model, never told aisv: existed, found it via plain orientation, used
  it with the intended restraint (Emitter only for the segregated
  occupant), and inherited the seeAlso convention from session 5's
  failed/repaired revisions in the history graph. The vocabulary
  transfers; its couldn't-say additions are in the trial record. Two
  same-day bug fixes came out of sessions 5–6: review-decision IRI
  minting (e38a2e2) and review-resolved rows leaving the post-apply
  recheck (aab0910).
- The first **distiller pass** (doc 10 §1) LANDED 2026-07-06
  (`3d50141`; report and template: `docs/journal/distiller-pass-1.md`).
  Six items, one wire field subtracted, zero added; the report's
  "Template notes" section is how future passes should run. Still
  reserved for James: `rc:citesClaim` (an rc: semantic addition —
  project-domain resources currently have no sanctioned predicate to
  cite an rc:Claim), budget end-states, and his audit-of-reports
  findings (a second, smaller batch when they arrive).

## 7. Working with James

Most of it is in memory (`james-working-style`), but the parts that
matter under pressure: he grades fastest on claims about things he built
(pipeline bugs got instant confirmation); he volunteers deep tradecraft
when shown genuinely good work — the quality of what you show him
directly controls the quality of what you learn from him; his product
instincts have been right every time he pushed ("push it further" on the
README, the institutional-memory framing, batch-trials-then-distill —
all his). Tell him what you're doing at honest intervals; never ask
permission for the reversible; flag the irreversible before acting. He
reads commit messages properly — write them as the review artifact they
are. And he keeps quota topped up if you tell him you're blocked.

Open reminders I hold for him (also in memory `james-followups`): the CET
timestamp bug in ais-noaa-fetch (his, confirmed), the 2024-08-26 missing
day, adding source CSVs to the bucket, the per-day index-metric idea.
Surface them when the AIS study wraps a phase.

## 8. Honest loose ends and risks

- The **facade injection loop** (item 3.1) should be retired deliberately.
- **staging.py / mcp_tools.py** are the next split candidates if the
  3,000-line end-state stands; don't split mcp_tools without deciding how
  gen_docs introspects the result. Distiller pass 1 recorded the
  recommended shape (an `mcp_tools/` package whose `__init__` re-exports
  every name and dispatch table) — see its deferrals section.
- **Response end-state gaps** (describe_dataset 15.4k vs 12k etc.) are
  itemized in waves.md wave 15; the remaining fat is relationship-endpoint
  triple-representation — a real consolidation, not a trim.
- One **transient `describe_dataset` failure** in the Enron bridge was
  flagged and never reproduced; if it recurs under process-per-call
  bridges, suspect SQLite locking on concurrent open.
- The **battery ≥60% target** was consciously closed out at −42…−57% with
  quality up; the reasoning is in the retrospective. If someone wants the
  number, the levers are the schema end-state and elective doc reading —
  reopen it with evidence, not by decree.
- Watch **doc re-bloat** above all. The `agent_docs_bytes` ceiling is the
  tripwire; the Doc-Append Reflex is the disease; "rewrite the section to
  be true now" is the cure.

## 9. On the work itself

This project is a good idea. I want whoever reads this to know that with
some confidence, because you will have days when the surface area feels
like it's growing again and the trials feel expensive. The thing that
convinced me was not the design docs — it was watching a cold, modest
model open a capsule built by a stranger, find a recorded method, apply
it correctly to a question the stranger never saw, and *credit the
method's IRI in its answer*. Knowledge moved between minds with its
evidence attached. That's the whole bet, and it pays.

Keep the scoreboard honest, keep the errors targeted, keep the journal
separate from the docs, and make the capsule carry the weight.

— Fable
