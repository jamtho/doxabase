from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from doxabase import DoxaBase
from doxabase.mcp_tools import load_example_fixtures_tool


CAPSULE = Path("/tmp/doxabase-adversarial-field-trial.sqlite")
REPORT = Path("/tmp/doxabase-adversarial-field-trial-report.md")
AGENT = "urn:doxabase:adversarial-field-trial-agent"


def main() -> None:
    if CAPSULE.exists():
        CAPSULE.unlink()

    db = DoxaBase.create(CAPSULE, overwrite=True)
    loaded = load_example_fixtures_tool(db, replace=True)

    table = _choose_ais_table(db)
    description = db.describe_dataset(table.iri)

    claim = db.record_claim_observation(
        summary=(
            "Adversarial hunch: AIS broadcast identity may be composite, but "
            "fixture metadata does not prove a durable key."
        ),
        claim_text=(
            "AIS Daily Broadcast Positions may need MMSI plus time/path context "
            "for operational identity, but the current fixture evidence is too "
            "thin to promote that directly into the map."
        ),
        claim_kind="rc:InterpretationClaim",
        claim_targets=[table.iri],
        observed_asset=table.iri,
        observed_by=AGENT,
        evidence_summary=(
            "Scratch trial using DoxaBase fixture loading, describe_dataset, "
            "search, and context slicing."
        ),
        evidence_sources=[
            str(CAPSULE),
            "docs/agent/start-here.md",
            "docs/agent/staged-revisions.md",
        ],
        source_path=str(REPORT),
        source_kind="rc:DoxaBaseAPISource",
        confidence="rc:LowConfidence",
        observation_status="rc:Tentative",
    )

    pattern = db.record_pattern(
        summary="Composite identity hunch should stay reviewable.",
        pattern_text=(
            "The uncertain identity hunch belongs in observations, patterns, "
            "and staged alternatives before it becomes current-best map truth."
        ),
        rationale=(
            "The dataset has an MMSI caveat and event-row semantics, but no "
            "durable key evidence in the fixture."
        ),
        pattern_targets=[table.iri],
        supporting_claims=[claim.claim_iri],
        synthesized_by=AGENT,
        evidence_summary="Trial deliberately tested premature map promotion.",
        evidence_sources=[
            "docs/agent/start-here.md",
            "docs/agent/graph-roles.md",
            "docs/agent/patterns.md",
        ],
        source_path="docs/agent/start-here.md",
        source_kind="rc:DocumentationSource",
        confidence="rc:LowConfidence",
        pattern_stability="rc:EmergingPattern",
    )

    draft = db.stage_systematisation(
        summary="Composite identity hunch alternatives",
        intent=(
            "Preserve an awkward modelling hunch without prematurely making it "
            "map truth."
        ),
        anchors=[table.iri, claim.claim_iri, pattern.pattern_iri],
        rationale=(
            "The docs recommend observation, pattern, and staged-revision layers "
            "for uncertain modelling hunches."
        ),
        shared_context_summary=(
            "Trial-only vocabulary for a composite operational identity hunch."
        ),
        shared_additions=[
            {
                "graph": "ontology",
                "format": "turtle",
                "content": _shared_ontology(),
            }
        ],
        framings=[
            {
                "label": "Pattern-first hunch",
                "graph": "patterns",
                "content": _pattern_first(table.iri, claim.claim_iri),
                "stance": "rc:ExploratoryHunch",
                "review_note": (
                    "Preferred because the evidence is thin and the model is "
                    "awkward."
                ),
                "review_recommendation": "Keep staged; do not apply yet.",
            },
            {
                "label": "Premature map caveat candidate",
                "graph": "map",
                "content": _invalid_map_caveat(table.iri),
                "stance": "rc:CandidateRevision",
                "review_note": (
                    "This intentionally uses an invalid severity term to prove "
                    "that validation diagnostics stay visible."
                ),
                "review_recommendation": (
                    "Expected to fail validation; repair only if the map caveat "
                    "is genuinely wanted."
                ),
            },
        ],
        supporting_claims=[claim.claim_iri],
        supporting_patterns=[pattern.pattern_iri],
        validation_scope="all",
    )

    staged = [db.describe_staged_revision(rev.revision_iri) for rev in draft.staged_revisions]
    deep_lore = db.describe_context_slice(
        [table.iri],
        profile="deep_lore",
        max_triples=160,
        include_trig=False,
    )
    validation = db.validate_graph(scope="all")

    _write_report(
        loaded=loaded,
        table_label=table.label or table.iri,
        columns=[column.column_name for column in description.columns[:8]],
        claim_iri=claim.claim_iri,
        pattern_iri=pattern.pattern_iri,
        staged=staged,
        route_counts=deep_lore.route_counts,
        validation_conforms=validation.conforms,
    )

    print(REPORT)


def _choose_ais_table(db: DoxaBase):
    tables = db.list_entities(type="rc:Table", graph="map", limit=20).entities
    for table in tables:
        haystack = f"{table.iri} {table.label}".lower()
        if "dailybroadcasts" in haystack or "broadcast" in haystack:
            return table
    return tables[0]


def _shared_ontology() -> str:
    return """
@prefix ex: <https://example.test/adversarial-field-trial#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:CompositeOperationalIdentityHunch a rdfs:Class ;
    rdfs:label "Composite operational identity hunch" ;
    rdfs:comment "Trial-only vocabulary for an identity model that may explain fixture retrieval but is not ready as map truth." .

ex:identityHunchFor a rdf:Property ;
    rdfs:label "identity hunch for" ;
    rdfs:comment "Links a staged identity hunch resource to the dataset it pressures." .
"""


def _pattern_first(table_iri: str, claim_iri: str) -> str:
    return f"""
@prefix ex: <https://example.test/adversarial-field-trial#> .
@prefix rc: <https://richcanopy.org/ns/rc#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:identity-hunch-pattern a rc:Pattern, ex:CompositeOperationalIdentityHunch ;
    rdfs:label "Composite identity remains a hunch" ;
    rc:summary "Keep composite identity as a pattern-level hunch." ;
    rc:patternText "The selected table may require MMSI plus temporal or file context for operational identity, but fixture context does not prove the durable key." ;
    rc:rationale "This preserves the modelling pressure without editing map facts." ;
    rc:patternTarget <{table_iri}> ;
    rc:supportingClaim <{claim_iri}> ;
    ex:identityHunchFor <{table_iri}> ;
    rc:confidence rc:LowConfidence ;
    rc:patternStability rc:EmergingPattern .
"""


def _invalid_map_caveat(table_iri: str) -> str:
    return f"""
@prefix ex: <https://example.test/adversarial-field-trial#> .
@prefix rc: <https://richcanopy.org/ns/rc#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:identity-caveat-candidate a rc:KnownCaveat ;
    rdfs:label "Composite identity not confirmed" ;
    rc:summary "Possible composite identity caveat for the selected AIS table." ;
    rc:caveatText "Do not assume a single-column durable key until identity behavior is checked against source data." ;
    rc:severity rc:MediumSeverity ;
    rc:impact "Query planning should avoid deduplication or joins that assume a single-column durable key." ;
    rc:affectsDataset <{table_iri}> .

<{table_iri}> rc:hasCaveat ex:identity-caveat-candidate .
"""


def _write_report(
    *,
    loaded: dict[str, object],
    table_label: str,
    columns: list[str],
    claim_iri: str,
    pattern_iri: str,
    staged: list[object],
    route_counts: dict[str, int],
    validation_conforms: bool,
) -> None:
    lines = [
        "# DoxaBase Adversarial Field Trial",
        "",
        f"Scratch capsule: `{CAPSULE}`",
        f"Loaded fixture triples: `{loaded['total_imported']}`",
        f"Table: `{table_label}`",
        f"Columns sampled: `{', '.join(columns)}`",
        f"Claim: `{claim_iri}`",
        f"Pattern: `{pattern_iri}`",
        f"Whole-capsule validation conforms: `{validation_conforms}`",
        (
            "A staged candidate can fail preview validation without changing "
            "whole-capsule validation, because staged patches are not applied "
            "to the current graphs."
        ),
        "",
        "## Staged Alternatives",
    ]
    for description in staged:
        lines.extend(
            [
                "",
                f"- `{description.label}`",
                f"  - IRI: `{description.iri}`",
                f"  - stance: `{description.revision_stance}`",
                f"  - conforms: `{description.validation_conforms}`",
                f"  - recommendation: {description.review_recommendation}",
            ]
        )
        for result in description.validation_results:
            messages = "; ".join(result.messages)
            lines.append(f"  - validation: {messages}")
    lines.extend(
        [
            "",
            "## Deep-Lore Route Counts",
            "",
            "```text",
            "\n".join(f"{key}: {value}" for key, value in sorted(route_counts.items())),
            "```",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
