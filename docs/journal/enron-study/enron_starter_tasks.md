# Starter Tasks For Future Agents

Use this checklist when starting a new analysis from the Enron DoxaBase store.
It assumes the files live in `/tmp/doxabase-enron-clean.pClwOo`.

## 1. Verify The Store

- Run `verify_enron_handoff.py` if you are using the exported bundle rather
  than the source capsule.
- Open `enron-emails.doxabase.sqlite` with the fresh checkout in
  `doxabase/`.
- Confirm `validate_graph(scope="all")` conforms before relying on the graph.
- Run `project_brief(limit=100, profile_candidate_limit=50)` and check that
  all four datasets are `ready_for_query_planning`.

## 2. Pick The Representation

- Use `eml_messages` for broader message coverage and parsed body text.
- Use `xml_messages` when native path/hash metadata is more important.
- Treat XML as a strict subset of EML by `doc_id`.
- Handle the 7,132 EML-only blank-source rows as a named special population.

## 3. Name The Population

- Start from the named logical views in `enron_analysis_views.md`.
- Prefer plausible-date populations for time-series work.
- Prefer message-like populations for communication networks and NLP.
- Exclude or stratify calendar/contact/meeting-like rows when they would distort
  message analyses.
- Record the exact view or filter used with every count, model, or chart.

## 4. Join Attachments Correctly

- Join attachment rows with `parent_doc_id -> doc_id`.
- Use attachment tables for exact attachment counts.
- Do not trust XML `attachment_count` as an exact row count; it disagrees with
  counted attachment rows for 3,128 messages.
- Use XML `native_hash` for attachment duplicate-content analysis.

## 5. Normalize Before Modeling

- Normalize empty strings and nulls together for text, folder, subject, and
  recipient fields.
- Filter or flag implausible message dates before temporal analysis.
- Lowercase and normalize attachment extensions.
- Preserve custodian and folder/location family as primary strata.
- Deduplicate globally but retain custodian/folder provenance.

## 6. Be Honest About Communication Coverage

- Report sender/recipient extractability before building networks.
- Treat none-to-none domain classes as parser-coverage gaps, not as evidence of
  no communication.
- Compare EML and XML sender fields before choosing one representation.
- Keep Exchange/X.500-style sender markers separate from internet email
  addresses.

## 7. Be Careful With Text Surfaces

- Decide whether NLP uses `body` or `body_top`.
- `body_top` removes quoted original-message material but is blank more often.
- `body` has broader coverage but can include reply chains and quoted material.
- Record the chosen surface and text-readiness denominator in the result.

## 8. Suggested First Questions

- What changes if I use EML versus XML for the same `doc_id` overlap?
- Which custodians and folder families dominate my population?
- Are my top months driven by calendar rows or actual message-like rows?
- How much of my population has usable sender and recipient domains?
- Are duplicate `message_id`, duplicate body, or duplicate attachment-hash
  groups driving a result?

## 9. Useful DoxaBase Calls

```python
db.project_brief(limit=100, profile_candidate_limit=50)
db.describe_dataset("https://example.test/enron-emails#eml_messages")
db.describe_dataset("https://example.test/enron-emails#xml_messages")
db.describe_context_slice(
    ["https://example.test/enron-emails#eml_messages"],
    profile="dataset_brief",
)
db.list_entities(type="rc:Pattern", graph="patterns", limit=50)
```

## 10. Stop Conditions

- Do not publish an analysis without naming the population and representation.
- Do not publish network results without sender/recipient extraction coverage.
- Do not publish time-series results without plausible-date filtering and
  folder-family stratification.
- Do not publish attachment counts from XML message metadata alone.
