# Enron Case Study — Handoff Corpus (repo copy)

Repo copy of the Enron DoxaBase case-study handoff (original:
/home/codex/enron-doxabase-handoff). The graded trial record is
`docs/journal/trials/2026-07-enron-case-study.md`; the rendered capsule
report is `docs/journal/ais-study/reports/enron-capsule-report.html`.

Included: all narrative docs (case-study report, docs overview, query
cookbook, analysis views, Western power policy analyses, starter tasks,
code-owner feedback), the importable TriG exports + handoff manifest,
analysis JSONs, the verify script, and the visuals.

Deliberately omitted: `enron-emails.doxabase.sqlite` (31MB binary — the
TriG export is the designed portable form; reconstruct via
import_bundle) and `enron_knowledge_store_revision_snapshots.json`
(11MB, regenerable). Both remain at the original path.

Shareability: scanned for credential values and secret patterns
2026-07-10 (clean); the underlying corpus is the public Enron email
dataset (FERC release).
