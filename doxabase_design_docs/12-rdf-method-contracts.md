# Design Doc 12: RDF Method Contracts

**Date**: 2026-07-12 (Fable's last day — written as the opening
position of a live design session with James, who has been thinking
about this pattern for a long time in other work)
**Status**: Position + decision points. A pilot experiment is running
against it (see §7).
**The idea, in James's framing**: use the graph to define high-level
behavioural contracts for algorithms; agents fill in the
accidental-but-still-necessary code that follows the RDF-expressed
spec; the model comes in successively more concrete layers, bottoming
out in natural language. RDF is the right basis because it lets those
layers reference each other — and, crucially here, reference the
capsule's described world.

---

## 1. Why this lands on prepared ground

The field study's recorded methods (M1–M12) already have a de facto
three-part anatomy, held together by convention:

1. a prose contract (what it does, why it works, failure modes) in
   the pattern text;
2. executable SQL, embedded in the same pattern;
3. caveats, linked, carrying the known lies.

Two forces now push the contract layer toward structure. First, the
**regeneration need**: the state-vs-ephemera architecture says frames
are cache and methods are knowledge — but "the method" is currently
one DuckDB dialect realization. Second, the **parameter provenance
need**: session 12 ran a 4,710-window survey to validate M11's
thresholds, and today those hard-won numbers live as literals inside
SQL strings. A threshold that cost a survey deserves to be a graph
citizen with its evidence attached.

## 2. The layer model (proposal)

- **L0 — natural language** (`rdfs:comment`): the bottoming-out.
  Always present; never load-bearing alone for anything a machine
  must do. (This is also where James's round-6 "prose as an epistemic
  rung" instinct lives: L0-only methods are the smell that marks
  future L1 candidates.)
- **L1 — semantic contract**: what the method consumes and produces,
  grounded by IRI in the capsule's described world:
  - inputs: dataset/column IRIs from the map (already described!),
    upstream method IRIs (`dependsOn` — M8 consumes M4 events × M7
    spans; today that composition is prose);
  - outputs: what the rows MEAN — e.g. "rows representing
    aisv:DwellPeriod-shaped intervals, one per (mmsi, contiguous
    stationary run)", including grain and keys;
  - invariants: checkable behavioural promises ("every input row lands
    in exactly one output interval or the exclusions table"; "output
    count is monotonic in the SOG threshold"); each invariant is a
    future generated test;
  - failure modes: links to the existing caveats (no new machinery).
- **L2 — parameters**: named constants as resources — value, unit,
  role, and above all **evidence**: M12's `sog_threshold = 0.5 kn`
  cites the session-13 rationale; M11's `radius_berth_max = 20 m`
  cites the session-12 survey plots. assessedAt/assessmentDataWindow
  apply, so thresholds age visibly as coverage grows. Changing a
  parameter becomes a staged revision with provenance, not a code
  edit.
- **L3 — realization**: the concrete SQL (or later: Spark, Python),
  now explicitly labelled as ONE realization of the L1+L2 contract,
  carrying engine + dialect + code-version. `derivedFromRun` then
  points at (contract, parameters, realization, data window) — the
  complete provenance quadruple for any frame.

## 3. What this buys, concretely

1. **Regeneration**: an agent given L1+L2 writes L3 for a new engine;
   the invariants tell it when it has succeeded. (The pilot in §7
   tests exactly this.)
2. **Cheap transfer**: a cold agent reads L1 to decide whether a
   method applies — today it reads SQL. Orientation cost drops for
   every future session.
3. **Trustable thresholds**: the expert's validation doctrine
   ("humans trust thresholds through plots") gets a permanent home —
   the plot IS the parameter's evidence, one hop away, forever.
4. **Honest composition**: M-method dependency becomes queryable
   structure. "What breaks downstream if M7's taxonomy changes?" stops
   being archaeology.
5. **The determinism principle completed**: frames were already
   regenerable in principle; now the thing that regenerates them is
   itself inspectable, evidenced, and reconsiderable knowledge.

## 4. What this must NOT become (boundaries)

- **No relational algebra in RDF.** The contract describes behaviour
  and meaning, never SQL syntax. The moment someone proposes
  `mc:SelectClause`, this project has failed.
- **No a-priori contract ontology.** Same law as the vocabulary:
  distill the contract terms FROM M11/M12/M9 as they are actually
  written, ≥2-method justification per term. Session 5 proved the
  order: cases first, vocabulary second.
- **Project-local first.** A small `mc:` (method-contract) vocabulary
  in the study capsule's ontology graph. It touches `rc:` only if the
  second domain (the private case study's reconciliation queries — a
  perfect stress test, being join-heavy and legally sensitive about
  its denominators) independently needs the same terms.
- **L0 stays mandatory.** The natural-language layer is not residue;
  it is the layer humans audit. A contract whose comment disagrees
  with its invariants is a bug in the contract.

## 5. Decision points for James (the session's live questions)

1. **Grain of invariants**: property-style assertions in RDF (cheap,
   checkable by generated SQL) vs full executable check-queries stored
   like the method SQL (heavier, more precise)? My lean: start with
   3–5 property-style invariants per method, promote to executable
   checks only where a property catches a real regression.
2. **Where parameters live**: on the method (simple) vs free-standing
   resources shared across methods (M7 and M12 both have SOG
   thresholds — same number, DIFFERENT justifications, so my lean is
   free-standing but method-scoped names, no premature sharing).
3. **Realization storage**: keep SQL in the pattern text (status quo,
   diff-friendly) vs as its own resource linked from the contract? My
   lean: own resource — it makes "two realizations, one contract"
   representable, which is the whole point.
4. **How far does regeneration authority go**: may an agent regenerate
   L3 and RUN it against live data unreviewed, or is regenerated code
   always staged behind an invariant-check report? My strong lean:
   the latter, always — code is a claim, and claims get evidence
   before promotion.

## 6. Relationship to James's wider pattern

His generalization (essential model in layers → agent supplies
accidental code → contracts as the face of code) is bigger than this
project: it is a software-engineering methodology where the spec is a
knowledge graph. This doc deliberately scopes to analytical methods
over described data, because that is where the capsule already
supplies the grounding (datasets, columns, caveats, evidence) that
makes contracts more than documentation. If it works here, the
generalization has a working example with measurable transfer — which
is worth more to the wider idea than a framework would be.

## 7. The pilot (running as this doc is written)

Express M12's contract as L1+L2 in the study capsule (project-local
mc: terms, distilled from how M12/M11/M9 are actually written); then a
SEPARATE cold agent regenerates the extraction SQL from the contract
alone (never seeing session 13's SQL) and runs it on the same
457-MMSI sample. Success = the recall table reproduces within
tolerance; the diff between regenerated and original behaviour is the
measure of what the contract failed to say — which is the real
deliverable: an empirical list of what contracts must express, learned
the same way everything else in this project has been.
