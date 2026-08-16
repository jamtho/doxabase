# Live-Retrieval Trial (ENRON-2) — run record (coordinator-maintained)

- 2026-08-16: protocol committed BEFORE any arm launch. SHA-256:
  3ea2928c70ed20ceba60ae8b13796207aa12f384483e9b8b20d777b4e91b7809
- Arm/preparer/measurer/judge model, recorded before first launch
  per §4: claude-sonnet-5 (all five graded-path agents).
- Launch order: E2S (static) first, then E2L (live), sequential.
- Window assignment executed mechanically per §3: capsule-copy hash
  first hex digit e (even) → E2S=W1 (2001-H1), E2L=W2 (2001-H2).
- 2026-08-16: E2S (static) complete — 21 episodes, 2 person-claims,
  zero arcs (explicit refusal, no in-window terminus), capsule
  conforming with zero staged debt. Working dir intact for the
  freeze. E2L launches next, sequential per §4.
