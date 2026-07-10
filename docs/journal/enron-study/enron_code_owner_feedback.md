# DoxaBase Code Owner Feedback From The Enron Trial

This feedback is about DoxaBase product and API ergonomics observed while
building the Enron Emails knowledge store. It is separate from the data
findings in the case-study report.

## High-Impact Improvements

1. Add a Parquet ingestion helper.

   The trial needed custom scripts to turn four Parquet files, 60 columns, and
   profiler outputs into datasets, columns, physical layout, profile records,
   observations, evidence, and caveats. A helper that accepts Parquet metadata
   plus aggregate profiling results would make this workflow much easier to
   repeat.

2. Add first-class S3 bucket and prefix modeling.

   The user naturally described the source as an S3 bucket. The available
   storage helper accepted `location_kind="prefix"` but rejected a bucket-shaped
   kind. A dedicated object-store route helper, or a documented bucket/prefix
   shape, would remove guesswork.

3. Make relationship enum values obvious.

   `record_map_relationship` expects compact values such as `foreign_key` and
   `shared_identifier`, while ontology-facing names suggest terms such as
   `rc:ForeignKey`. Accepting both, or documenting the compact values in
   examples and errors, would help agents author conforming graph facts.

4. Clarify column transformation modeling.

   Modeling `body -> body_top` as a direct derivation relationship failed
   validation. The graph still records the finding as caveat/pattern/claim lore,
   but the intended path for column-to-column transforms should be documented.

5. Add an export validation gate.

   The workflow can export an invalid graph if the caller forgets to validate
   first. A `require_validation_conforms=True` option, or a prominent warning
   when exporting after a failed validation, would protect unattended workflows.

## Workflow And Documentation Improvements

6. Provide a profile-to-capsule CLI example.

   A command or cookbook for "local Parquet files -> DoxaBase capsule" would be
   a high-value starter path. The scripts from this trial can serve as a
   prototype for schema capture, aggregate profiles, caveats, and query
   readiness.

7. Improve external-script import guidance.

   Running scripts outside the repo required explicit `PYTHONPATH` setup. A
   short note about editable installs or supported script invocation would avoid
   namespace confusion.

8. Add a non-secret credential-reference model.

   The store intentionally omitted credentials but kept enough storage context
   to know the bucket route. A standard way to say "credentials exist locally
   but are intentionally not recorded" would make this safer and more uniform.

9. Add a compact status for completed profile drafts.

   `project_brief` reported profile drafts with zero recommendations after map
   facts had already been recorded. That is accurate, but easy to misread. A
   status like "profile evidence captured; no pending map recommendations"
   would be clearer.

10. Add query-cookbook and analysis-view helpers.

   Case-study stores need executable on-ramps. Helpers for recording named SQL
   views, row counts, caveats, and starter query recipes would let agents
   preserve analysis denominators without pretending logical views are physical
   datasets.

11. Add a domain-network profiling helper.

   Communication analysis needs extractability denominators and aggregate
   domain-pair counts without preserving individual addresses. A helper for
   this shape would support email, chat, and transaction-like datasets.

## What Worked Well

- The graph roles mapped well to the work: durable schema/storage facts in
  `map`, full-scan measurements in `observations`, interpretations in
  `patterns`, and support in `evidence`.
- Validation caught a bad modeling choice before export.
- `describe_dataset`, `project_brief`, export, handoff import, and staged
  revision snapshot preservation all worked for a multi-pass case study.
- Scanner-clean exports were possible without recording credentials or raw
  message bodies.
