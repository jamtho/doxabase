# Ontology Primer

The Rich Canopy base ontology uses the `rc:` prefix:

```text
https://richcanopy.org/ns/rc#
```

It is a small shared vocabulary for data-project modelling. It is not a closed world and not a complete model of all possible data domains.

Use `rc:` terms for shared structural concepts:

- `rc:Dataset`, `rc:Table`, `rc:Column`, `rc:ColumnGroup`
- `rc:ValueType`, `rc:PhysicalType`, `rc:AllowedValues`, `rc:ValueRange`
- `rc:ForeignKey`, `rc:SharedIdentifier`, `rc:Derivation`, `rc:Aggregation`
- `rc:KnownCaveat`, `rc:Observation`, `rc:Claim`, `rc:Pattern`, `rc:Evidence`
- `rc:PhysicalLayout`, `rc:PartitionScheme`, `rc:RowOrdering`
- `rc:LayoutVerificationStatus` for path/layout confidence and verification

To list a controlled vocabulary's members (physical types, value types,
confidence levels, statuses), call
`list_entities(type="rc:PhysicalType", graph="ontology")` — the `ontology`
selection includes the shipped `base_ontology`. The default `graph="map"`
holds project facts, not vocabulary, so it returns 0 for these types.

Use project namespaces for domain-specific ideas:

- AIS value types can live under `ais:`.
- Polymarket value types can live under `pm:`.
- A client project can define any namespace it needs.

Useful distinction:

- Declared allowed values belong to the model, using `rc:AllowedValues`.
- Observed values from a profiler belong to observations, using
  `rc:Observation` or `rc:ProfileObservation`; counted values can be paired as
  `rc:ObservedValueFrequency` resources, while scalar metrics such as observed
  minimum/maximum/mean values can be paired as `rc:ObservedProfileMetric`
  resources. Use `rc:profileMetricTarget` when a scalar metric is specifically
  about a resource narrower than the whole profile observation.
- Project-specific profile metric kinds can start as ordinary project IRIs in
  scratch observations. When later agents should recognize the metric as shared
  project vocabulary, add a labelled term in the project `ontology` graph rather
  than the base `rc:` ontology.
- Syntheses over related observations or claims belong to patterns, using
  `rc:Pattern`.

The base SHACL shapes validate common authoring mistakes in `rc:` usage. They are open and do not reject client-defined terms.
