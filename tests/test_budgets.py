"""Enforce the distillation program's budget ceilings in the ordinary gate.

Ceilings live in exactly one place: ``BUDGETS`` in ``tools/scoreboard.py``.
This test recomputes the same metrics through the scoreboard's functions so a
regression fails ``pytest`` even when nobody ran the scoreboard by hand.

Per `doxabase_design_docs/07-distillation-program.md`: ceilings only ratchet
toward the end-state targets; loosening any ceiling requires James.
"""

from __future__ import annotations

import pytest

from tools import scoreboard


@pytest.fixture(scope="module")
def metrics() -> dict[str, object]:
    return scoreboard.measure_all()


@pytest.mark.parametrize("metric", sorted(scoreboard.BUDGETS))
def test_budget(metrics: dict[str, object], metric: str) -> None:
    actual = metrics[metric]
    ceiling = scoreboard.BUDGETS[metric]
    assert isinstance(actual, int)
    assert actual <= ceiling, (
        f"{metric} = {actual:,} exceeds the distillation budget {ceiling:,}. "
        "Shrink the surface; do not loosen the ceiling (that requires James — "
        "see doxabase_design_docs/07-distillation-program.md)."
    )


def test_every_budget_has_an_end_state() -> None:
    assert set(scoreboard.BUDGETS) == set(scoreboard.END_STATE)
