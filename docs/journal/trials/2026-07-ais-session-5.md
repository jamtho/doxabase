# AIS Real-Work Study — Session 5: The Vocabulary Distillation (2026-07-06/07)

Fable distiller; the ontology-pack experiment (doc 10 §4) run on
empirical rails. Deliverables: 25-term `aisv:` vocabulary (7 classes, 18
properties, every term ≥2-story-justified with citations in its
rdfs:comment), staged into the ontology graph via the full
stage→dry-run→apply→validate loop; three diverse stories re-expressed as
13 aisv: map resources via a second staged revision; the couldn't-say
list; VOCAB-NOTE.md design note for James. Graph conforms; staged queue
empty. Artifacts: /home/codex/ais-study/{VOCAB-NOTE.md,JOURNAL-5.md}.

## Experiment verdict

- **Zero data queries needed** — every justification already existed as
  recorded knowledge. The distillation ran entirely on the capsule.
- The stories FORCED the design's best insight: `aisv:AisIdentity` (the
  MMSI-keyed, year-frozen, self-reported identity slot) is distinct from
  `aisv:Emitter` (a physical transmitting object) — five shared-MMSI
  stories made anything simpler untenable. A priori design would likely
  have started from "Vessel" and been wrong.
- The feed's pathologies live in the semantics honestly:
  `aisv:apparentDate` vs `aisv:datingQuality` encodes the Jan-1 artifact;
  `ambiguous_ballast` is a mandatory cargoDirection value.
- The staging preview caught a shapes violation BEFORE the map was
  touched (twice earned its keep); the failed candidate was closed
  properly as superseded.
- Couldn't-say list = the v2 roadmap: voyages/excursions, recurring
  event clusters / trade lanes (the biggest gap), tempo metrics,
  Place-as-resource, data-quality artifacts as events.

## Product findings

1. **FIXED same-day**: `resolution_revision_iri` on review decisions
   mints a NEW history record; passing an existing revision IRI appended
   duplicate single-cardinality fields onto that row (7 SHACL
   violations; the agent repaired history via careful TriG surgery,
   documented in JOURNAL-5.md). The recorder now refuses pre-existing
   IRIs with a targeted error; regression-tested.
2. For James (rc: kernel decision): base shapes reserve
   `rc:supportingClaim`/`rc:hasClaim`, so project-domain resources have
   no sanctioned predicate to cite an rc:Claim — the distiller used
   rdfs:seeAlso. Proposal: an open-domain `rc:citesClaim`.
3. Distiller items: no staged route exists for history-graph repair;
   review_decision's enum only discoverable via error.
