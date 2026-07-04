from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from doxabase import DoxaBase
from examples._runtime_paths import example_artifact, reset_file


CAPSULE = example_artifact(
    "staged-semantic-repair-smoke",
    "/tmp/doxabase-staged-semantic-repair-smoke.sqlite",
    filename="capsule.sqlite",
)
BASE = "https://example.test/staged-semantic-repair-smoke#"
RC = "https://richcanopy.org/ns/rc#"


def main() -> None:
    reset_file(CAPSULE)

    db = DoxaBase.create(CAPSULE, overwrite=True)
    orders = f"{BASE}Orders"
    fulfillment_events = f"{BASE}FulfillmentEvents"
    db.record_map_dataset(
        orders,
        label="Orders semantic-repair smoke table",
        is_table=True,
        row_semantics="rc:SnapshotRow",
    )
    independent = db.stage_graph_revision(
        summary="Add Fulfillment Events table",
        rationale="Independent table proposal staged before row-grain review.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix rc: <{RC}> .

                    <{fulfillment_events}> a rc:Dataset, rc:Table .
                """,
            }
        ],
        revision_anchors=[fulfillment_events],
    )
    alternatives = db.stage_systematisation(
        summary="Explore Orders row-grain alternatives",
        intent=(
            "Keep competing row-semantics framings reviewable while recovery "
            "separates mechanical drift from semantic same-slot repair."
        ),
        anchors=[orders],
        framings=[
            _row_semantics_framing(
                orders,
                label="Event rows",
                replacement="rc:EventRow",
                recommendation="Preferred for this smoke run.",
            ),
            _row_semantics_framing(
                orders,
                label="Aggregate rows",
                replacement="rc:AggregateRow",
                recommendation="Competing alternative.",
            ),
        ],
        validation_scope="all",
    )
    event_rows = alternatives.staged_revisions[0]
    aggregate_rows = alternatives.staged_revisions[1]
    initial_plan = db.plan_staged_revision_recovery(current_staged_work_only=True)
    applied_event = db.apply_staged_revision(event_rows.revision_iri)
    stale_plan = db.plan_staged_revision_recovery(
        current_staged_work_only=True,
        drift_detail="exact",
    )
    dry_run = db.restage_staged_revisions(
        [independent.revision_iri, aggregate_rows.revision_iri],
        dry_run=True,
    )
    restaged_independent = db.restage_staged_revision(independent.revision_iri)
    restaged_independent_check = db.check_staged_revision_apply(
        restaged_independent.revision_iri,
    )
    db.apply_staged_revision(restaged_independent.revision_iri)
    repair_draft = db.draft_staged_revision_rebase(aggregate_rows.revision_iri)
    if repair_draft.preferred_action is None:
        raise RuntimeError("expected same-slot repair draft to include an action")
    repair = db.stage_map_assertion_change(**repair_draft.preferred_action.args)
    repair_check = db.check_staged_revision_apply(repair.staged_revision.revision_iri)
    if repair_check.next_action is None:
        raise RuntimeError("expected repaired successor to carry a next action")
    handled_source = db.describe_staged_revision(
        aggregate_rows.revision_iri,
        include_current_apply_check=True,
    )
    if handled_source.current_restaged_by is None:
        raise RuntimeError("expected stale source to point at its repair successor")
    final_plan = db.plan_staged_revision_recovery(current_staged_work_only=True)
    validation = db.validate_graph(scope="all")

    print("# DoxaBase Staged Semantic Repair Smoke")
    print(f"Capsule: {CAPSULE}")
    print(f"Initial mutation frontier count: {len(initial_plan.mutation_frontier_iris)}")
    print(
        "Initial requires recheck after each apply: "
        f"{initial_plan.requires_recheck_after_each_apply}"
    )
    print(
        "Post-apply recheck subset count: "
        f"{len(applied_event.post_apply_recheck_revision_iris)}"
    )
    print(f"Recovery queues: {stale_plan.next_action_queue_item_counts}")
    print(f"Mechanical restage candidates: {stale_plan.would_restage_revision_iris}")
    print(
        "Helper mutation actions: "
        f"{[action.tool for action in stale_plan.helper_mutation_frontier_actions]}"
    )
    print(
        "Same-slot skip reasons: "
        f"{dry_run.not_restageable_revision_iris_by_reason}"
    )
    print(f"Independent successor status: {restaged_independent_check.status}")
    print(f"Repair draft: {repair_draft.draft_status} / {repair_draft.draft_kind}")
    print(
        "Repair successor status: "
        f"{repair_check.status} / {repair_check.next_action.action_label}"
    )
    print(f"Alternative gate: {repair_check.alternative_gate.status}")
    print(
        "Alternative semantic review required: "
        f"{repair_check.alternative_gate.semantic_review_required}"
    )
    print(
        "Handled stale source current successor: "
        f"{handled_source.current_restaged_by.iri}"
    )
    print(f"Final recovery queues: {final_plan.next_action_queue_item_counts}")
    print(
        "Final semantic review counts: "
        f"{final_plan.semantic_review_required_queue_counts}"
    )
    print(f"Validation conforms: {validation.conforms}")


def _row_semantics_framing(
    orders: str,
    *,
    label: str,
    replacement: str,
    recommendation: str,
) -> dict[str, object]:
    return {
        "label": label,
        "additions": [
            {
                "graph": "map",
                "content": f"""
                    @prefix rc: <{RC}> .

                    <{orders}> rc:rowSemantics {replacement} .
                """,
            }
        ],
        "removals": [
            {
                "graph": "map",
                "content": f"""
                    @prefix rc: <{RC}> .

                    <{orders}> rc:rowSemantics rc:SnapshotRow .
                """,
            }
        ],
        "review_recommendation": recommendation,
    }


if __name__ == "__main__":
    main()
