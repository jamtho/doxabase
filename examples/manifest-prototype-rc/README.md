# Manifest Prototype RC Fixtures

This directory contains hand-converted fixtures from `../manifest-prototype` into the draft Rich Canopy `rc:` ontology.

The purpose is to test whether the base ontology can carry real project-specific models without forcing every domain idea into `rc:`. Shared modelling terms use `rc:`. Domain terms and project instances use fixture namespaces such as `ais:` and `pm:`.

## Files

- `mnf-to-rc-mapping.md` documents the main Manifest-to-Rich-Canopy term mapping.
- `ais.trig` converts representative AIS/NOAA graph content.
- `polymarket.trig` converts representative Polymarket graph content.

## Graph Roles

The TriG fixtures use these graph IRIs as stand-ins for DoxaBase graph roles:

- `rcg:ontology` for project/domain value types and functions.
- `rcg:map` for the current project data map.
- `rcg:observations` for point-in-time or migration-time observations.
- `rcg:evidence` for source references supporting the converted assertions.

The immutable base ontology and base shapes remain in `../../ontology/rc_core.ttl` and `../../ontology/rc_shapes.ttl`.

## Scope

These are representative fixtures, not full mechanical ports. They preserve the modelling pressure that matters for the base ontology: tabular assets, columns, value types, embedded structures, layout, partitioning, caveats, derivations, aggregations, foreign keys, and shared identifiers.
