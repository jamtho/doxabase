# Enron Emails DoxaBase Case Study Report

Run directory: `/tmp/doxabase-enron-clean.pClwOo`

## Final Deliverables

- Capsule: `/tmp/doxabase-enron-clean.pClwOo/enron-emails.doxabase.sqlite`
- Project TriG export: `/tmp/doxabase-enron-clean.pClwOo/enron_knowledge_store.trig`
- Handoff manifest: `/tmp/doxabase-enron-clean.pClwOo/enron_knowledge_store_handoff_manifest.json`
- Handoff TriG: `/tmp/doxabase-enron-clean.pClwOo/enron_knowledge_store_handoff.trig`
- Revision snapshots: `/tmp/doxabase-enron-clean.pClwOo/enron_knowledge_store_revision_snapshots.json`
- Final summary: `/tmp/doxabase-enron-clean.pClwOo/enron_store_final_summary.json`
- Handoff verification summary: `/tmp/doxabase-enron-clean.pClwOo/enron_handoff_verify_summary.json`
- Latest handoff verification summary: `/tmp/doxabase-enron-clean.pClwOo/enron_handoff_verify_latest_summary.json`
- Handoff verification script: `/tmp/doxabase-enron-clean.pClwOo/verify_enron_handoff.py`
- Directory README: `/tmp/doxabase-enron-clean.pClwOo/README.md`
- Human docs overview: `/tmp/doxabase-enron-clean.pClwOo/enron_docs_overview.md`
- Future-agent starter tasks: `/tmp/doxabase-enron-clean.pClwOo/enron_starter_tasks.md`
- DoxaBase code-owner feedback: `/tmp/doxabase-enron-clean.pClwOo/enron_code_owner_feedback.md`
- Query cookbook: `/tmp/doxabase-enron-clean.pClwOo/enron_query_cookbook.md`
- Recommended analysis views: `/tmp/doxabase-enron-clean.pClwOo/enron_analysis_views.md`
- Profiling evidence:
  `/tmp/doxabase-enron-clean.pClwOo/enron_profile.json`,
  `/tmp/doxabase-enron-clean.pClwOo/enron_deep_profile.json`,
  `/tmp/doxabase-enron-clean.pClwOo/enron_advanced_profile.json`,
  `/tmp/doxabase-enron-clean.pClwOo/enron_analyst_profile.json`,
  `/tmp/doxabase-enron-clean.pClwOo/enron_network_time_profile.json`

I used a fresh clone at `/tmp/doxabase-enron-clean.pClwOo/doxabase` and avoided reading previous DoxaBase trial artifacts or existing local checkouts.

## What I Did

1. Cloned `git@github.com:jamtho/doxabase.git` into a fresh temp directory.
2. Read the current DoxaBase agent docs and helper APIs from that clone.
3. Listed the MinIO `enron-emails` bucket and copied the four Parquet objects into the clean temp run.
4. Profiled the Parquet files with PyArrow and DuckDB, using aggregate/full-scan queries and avoiding raw email body samples in evidence artifacts.
5. Built an initial DoxaBase capsule with project ontology terms, map facts, profiles, claims, caveats, relationships, patterns, and a history record.
6. Ran a deeper aggregate pass over EML/XML deltas, date alignment, address extraction coverage, threading/deduplication, attachment identity, text-surface readiness, and query on-ramp needs.
7. Ran an analyst-slicing pass over recommended logical populations, custodian skew, folder/location families, duplicate clusters crossing context, and attachment heavy tails.
8. Ran a communication/time pass over domain extractability, sender-recipient domain classes, monthly volume, calendar-driven spikes, and message-like population counts.
9. Augmented the capsule after each pass, validated, exported, and re-imported the handoff bundle into a fresh capsule to verify recovery.
10. Added a human handoff documentation layer: README, narrative docs overview, starter tasks, code-owner feedback, and a reusable handoff verification script.

## Final Store Contents

Final validation conforms with zero SHACL results.

- 4 datasets/tables
- 60 columns
- 1 S3-compatible storage route
- 112 observations
- 22 claims
- 19 patterns
- 58 evidence resources
- 4 graph revisions
- 787 map triples
- 117 project ontology triples
- 3,786 observation triples
- 345 pattern triples
- 322 history triples

All four datasets are `ready_for_query_planning` according to `project_brief`.
The final TriG and handoff exports reported zero sensitive-literal scanner hits.

Fresh handoff verification succeeded twice. The latest verifier run imported
the handoff manifest into
`/tmp/doxabase-enron-clean.pClwOo/enron-handoff-verify-latest.doxabase.sqlite`,
validated cleanly, and preserved the same key counts and query-readiness status.
Its machine-readable summary is
`/tmp/doxabase-enron-clean.pClwOo/enron_handoff_verify_latest_summary.json`.

The handoff manifest is scanner-clean with zero sensitive-literal hits, but it
still records `shareability_review_required`. Scanner-clean means the selected
export content did not match DoxaBase's credential-like graph-term patterns; it
is not a full review for user-specific paths, endpoint details, or confidential
project facts.

## Documentation Package

- `README.md` is the operational entry point and quick-start guide.
- `enron_docs_overview.md` is the short human narrative for deciding which file
  to read next.
- `enron_query_cookbook.md` provides DuckDB query patterns for the physical
  Parquet tables.
- `enron_analysis_views.md` defines stable logical populations and view SQL.
- `enron_starter_tasks.md` gives future agents a practical checklist.
- `enron_code_owner_feedback.md` isolates DoxaBase API and documentation
  recommendations from the Enron-specific findings.
- `verify_enron_handoff.py` re-imports the handoff manifest into a fresh
  capsule, validates it, compares key counts with the source capsule when
  available, and writes a JSON summary.

## Main Dataset Findings

- The bucket contains four ZSTD-compressed Parquet files written by Polars:
  `eml_messages` 1,234,387 rows, `eml_attachments` 493,395 rows,
  `xml_messages` 1,227,255 rows, and `xml_attachments` 493,384 rows.
- `doc_id` is the reliable message key. It is non-null and unique in both message tables.
- XML messages are a strict subset of EML messages by `doc_id`: 1,227,255 overlaps, 7,132 EML-only rows, no XML-only rows.
- The 7,132 EML-only rows form a coherent special subset: all have blank `folder` and blank `source_file`, span 31 custodians, and only 17 have attachments.
- All 151 custodians appear in both EML and XML message tables, but row counts are highly skewed. The largest slice is `kean-s` with 225,665 EML rows and 225,633 XML rows.
- Attachment joins are clean by `parent_doc_id -> doc_id` for both EML and XML attachment tables.
- EML `message_id` is not unique: 25,462 duplicate groups, 64,332 rows in duplicate groups, maximum 73 rows for one `message_id`.
- Duplicate clusters cross context: 7,490 duplicate `message_id` groups cross custodians; 121,335 duplicate non-empty body groups cross folders; 11,771 XML attachment-hash duplicate groups cross custodians.
- EML/XML overlapping timestamps mostly align: 1,226,990 of 1,227,255 overlapping rows match within one second, so many implausible date rows are shared source-data issues rather than representation-specific parse drift.
- Message dates still need filters. XML `date_sent` has severe parsed outliers from year 1316 through 9719; EML has 261 null dates and out-of-window rows.
- Folder/location families are analytically meaningful. `all documents`, `calendar`, `discussion threads`, `sent`, `contacts`, and blank folders have different body coverage, attachment rates, custodian coverage, and date-outlier profiles.
- Monthly volume has a calendar-driven spike. The largest plausible-date month is 2002-11 with 134,027 EML rows and 134,027 XML rows; in EML, 126,208 of those rows come from the calendar folder family.
- EML missing text often appears as empty strings rather than nulls, including recipients, subject, body, `body_top`, and folder.
- Regex email extraction is useful but incomplete. EML `to_addrs` is populated on 652,110 rows but regex email tokens appear in 215,775 rows; XML `to` is populated on 746,550 rows with regex tokens in 311,860 rows.
- Domain-level network matrices are coverage-limited. EML has 1,001,806 rows in the none-to-none sender/recipient domain class; XML has 895,661. These are parser-coverage gaps, not proof of no communication.
- Sender fields differ by representation: EML `from_email` is sparse, XML `from_` is display-name oriented, and some fields contain Exchange/X.500-style markers.
- XML `attachment_count` disagrees with counted attachment rows for 3,128 messages; aggregate `xml_attachments` for exact counts.
- Attachment counts have a heavy tail. Both EML and XML reach 260 attachment rows for one message; 4,525 messages have at least 10 attachments.
- Attachment extensions need normalization. After lowercasing, `doc`, `url`, `xls`, `pdf`, and `ppt` dominate, but blanks and case variants are common.
- XML `native_hash` is valuable for attachment duplicate-content analysis: 67,685 duplicate hash groups cover 417,668 attachment rows.
- `body_top` should be treated as a derived text surface. It equals `body` for 1,025,481 rows, is shorter for 208,906 rows, and removes the observed original-message marker entirely, but it is blank more often than `body`.

## Recommended Analysis Populations

The store now records named logical population counts:

- `eml_messages_plausible_1997_2004`: 1,210,548 rows
- `xml_messages_plausible_1997_2004`: 1,203,416 rows
- `eml_xml_doc_id_overlap`: 1,227,255 rows
- `eml_only_blank_source_subset`: 7,132 rows
- `eml_messages_with_body_text`: 739,872 rows
- `eml_messages_with_body_top_text`: 695,225 rows
- `eml_messages_with_regex_sender_email`: 97,929 rows
- `xml_messages_with_regex_sender_email`: 198,050 rows
- `eml_messages_plausible_message_like`: 980,561 rows
- `eml_messages_plausible_message_like_with_body`: 714,325 rows
- `eml_messages_plausible_message_like_with_body_top`: 670,649 rows
- `xml_messages_plausible_message_like`: 973,356 rows

The generated analysis-views file contains DuckDB view definitions for these populations plus attachment-count and folder-family views.

## Query Cookbooks

The query cookbook gives starter DuckDB query shapes for:

- registering the four Parquet tables;
- choosing EML versus XML message surfaces;
- applying date hygiene filters;
- joining attachments by `parent_doc_id`;
- using attachment tables for exact XML attachment counts;
- extracting sender/recipient domains with coverage caveats;
- choosing `body` versus `body_top`;
- threading/deduplication checks;
- normalized attachment extension and XML native-hash duplicate analysis.

The analysis-views cookbook adds named logical views for date, overlap, text-readiness, sender-email coverage, message-like rows, attachment counts, folder/location families, and monthly volume by folder family.

## What Went Well

- DoxaBase’s graph roles fit the task naturally: durable table/schema/storage facts went into `map`, full-scan measurements into `observations`, interpretations into `patterns`, and support into `evidence`.
- The map/profile/claim/pattern helper APIs were enough to build a useful store without hand-writing most RDF.
- Validation caught a bad modeling move when I tried to encode `body -> body_top` as a direct map derivation relationship. Moving that into caveat/pattern/claim lore produced a conforming store.
- `describe_dataset`, `project_brief`, export, and handoff import all worked against the resulting capsule.
- The privacy scanner did not flag the final exports, and credentials were intentionally omitted from storage-access metadata.

## What Went Badly Or Was Friction

- The sandbox required approvals for cloning, MinIO access, and dependency downloads. Expected, but it slowed iteration.
- `uv` initially tried to write under the home cache, which is read-only here. Setting `UV_CACHE_DIR` inside the temp run fixed it.
- Running scripts outside the repo required setting `PYTHONPATH` explicitly to the fresh clone.
- `record_map_storage_access` rejected `location_kind="bucket"`. Modeling the bucket as `location_kind="prefix"` worked, but bucket-shaped S3 storage is common enough to deserve a smoother route.
- `record_map_relationship` expects compact strings like `foreign_key` and `shared_identifier`, while the docs and ontology naturally lead agents to think in terms like `rc:ForeignKey`.
- The first attempt to model `body_top` as a derivation relationship failed SHACL because current relationship column constraints did not accept that shape. The validation message was helpful, but the intended column-derivation modeling path is not obvious.
- The current workflow makes bulk ingestion verbose. Recording four schemas, 60 columns, full profiles, caveats, patterns, and analysis views required multiple scripts.
- Exports can be run on an invalid graph if the caller does not gate on validation. I caught and fixed this, but an unattended workflow could preserve bad review artifacts.

## Recommendations For The DoxaBase Code Owner

1. Add a schema/table ingestion helper that can take Parquet metadata plus profiler results and create dataset, column, layout, and profile records in one transaction.
2. Either accept `rc:ForeignKey`/`rc:SharedIdentifier` in `record_map_relationship`, or make the compact enum values prominent in map-authoring docs and error examples.
3. Add first-class S3 bucket/prefix ergonomics. A `bucket` location kind or dedicated object-store route helper would match user expectations.
4. Provide a small CLI or example for “profile local Parquet files into a DoxaBase capsule.” The scripts in this run are a useful prototype.
5. Clarify the recommended model for column-to-column transformations such as `body -> body_top`. If direct map relationships are not intended, document the pattern/caveat route explicitly.
6. Add an optional export gate such as `require_validation_conforms=True`, or a prominent warning when exporting a graph whose latest validation failed.
7. Improve external-script import guidance. A note about `PYTHONPATH` or editable installs would prevent namespace confusion.
8. Consider a compact “profile evidence only, no map recommendations expected” status in `project_brief`; this capsule correctly has profile drafts with zero recommendations after map facts are already recorded, but the queue counts require interpretation.
9. Add a documented way to represent “credential reference intentionally omitted” for storage routes, so agents can preserve non-secret access context consistently.
10. Consider a query-cookbook or starter-plan artifact helper. Case-study stores often need executable on-ramps, not only graph descriptions.
11. Add an analysis-view helper for recording named logical populations, their SQL, row counts, and supporting caveats without forcing them to masquerade as physical datasets.
12. Consider a domain-network profiling helper that preserves extractability denominators and aggregate domain-pair counts without recording individual addresses.

## Recommendations For Future Agents Using This Store

- Start with `project_brief`, then `describe_dataset` for `eml_messages` or `xml_messages`.
- Use `doc_id` for message identity and `parent_doc_id` for attachment joins.
- Choose EML or XML deliberately. EML is broader and has parsed body text; XML has richer native path/hash metadata but is a strict subset.
- Treat the EML-only blank-source subset as special before comparing EML and XML.
- Name your analysis population before reporting any count, model, network, or NLP result.
- Normalize empty strings, date outliers, extension case, and sender representations before modeling.
- Treat custodian and folder/location family as primary strata in exploratory summaries.
- Report address-extraction coverage before building communication networks.
- Stratify monthly time-series by folder/location family; November 2002 is calendar dominated.
- Use message-like views when calendar/contact/meeting rows would distort NLP or network denominators.
- Deduplicate globally while preserving custodian/folder provenance.
- Use attachment tables for exact attachment counts, especially on the XML side.
- For attachment duplicate-content work, prefer XML `native_hash`.
- For NLP, record whether the analysis used `body` or `body_top`; neither is universally better.
