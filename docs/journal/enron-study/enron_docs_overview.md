# Human Overview Of The Enron DoxaBase Docs

This directory is a handoff package for a DoxaBase knowledge store built from
the MinIO `enron-emails` bucket. The core artifact is
`enron-emails.doxabase.sqlite`; the surrounding docs explain how to use it,
what the store learned, and where future work should start.

Start with `README.md` when you need orientation. It names the main files,
shows a minimal DoxaBase open/validate command, and lists the entry IRIs for
the four physical tables. It is intentionally short and operational.

Read `enron_doxabase_case_study_report.md` for the full narrative of the run.
That report explains how the data was copied from MinIO, how the Parquet files
were profiled, what was encoded into the capsule, what validated cleanly, and
what friction came from using the current DoxaBase API. It is the best single
document for understanding why the store is shaped the way it is.

Use `enron_query_cookbook.md` when writing DuckDB queries against the Parquet
files. It gives concrete query patterns for registering the four tables,
joining messages to attachments, choosing EML versus XML surfaces, filtering
dates, extracting communication domains, and handling `body` versus `body_top`.

Use `enron_analysis_views.md` when you need stable denominators. It defines
named logical populations such as plausible-date messages, EML/XML overlaps,
message-like rows, body-text-ready rows, sender-email-ready rows, attachment
counts, folder families, and monthly volume by folder family. These views are
important because counts shift materially depending on representation, date
filter, folder family, and text-surface choice.

Use `enron_starter_tasks.md` as the checklist for a future analysis agent. It
turns the findings into a practical sequence: validate the capsule, choose an
analysis population, check address-extraction coverage, stratify by folder and
custodian, and only then build models, networks, or NLP outputs.

Use `enron_code_owner_feedback.md` for DoxaBase product feedback. It is aimed
at the agent or maintainer who owns the DoxaBase codebase, not at Enron-email
analysts. It separates API/documentation friction from data findings.

Use `verify_enron_handoff.py` when you want to check that the exported handoff
bundle still imports into a fresh capsule. The script imports
`enron_knowledge_store_handoff_manifest.json`, validates the imported store,
compares key counts with the source capsule when available, and writes a JSON
summary.

The JSON profile files are evidence artifacts from the aggregate profiling
passes. They are useful for audit and follow-up exploration, but most users
should not begin there. Prefer the DoxaBase capsule, the report, and the two
query/view cookbooks.

The most important analytic lesson is simple: name the population before doing
data science. `doc_id` is the right message identity key and `parent_doc_id` is
the right attachment join key, but EML versus XML, plausible-date filters,
calendar/contact rows, body coverage, sender extraction, and duplicate handling
all change denominators enough to alter conclusions.
