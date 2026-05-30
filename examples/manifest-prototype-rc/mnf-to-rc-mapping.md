# Manifest to Rich Canopy Mapping

This note records the mapping used by the RC fixtures.

## Prefixes

- `mnf:` -> `rc:` for shared/base modelling terms.
- `ais:` stays a project/domain namespace for AIS value types, datasets, columns, caveats, and functions.
- `pm:` stays a project/domain namespace for Polymarket value types, datasets, columns, caveats, and functions.

## Main Renames

| Manifest term | RC term | Note |
| --- | --- | --- |
| `mnf:Dataset` | `rc:Dataset`, often also `rc:Table` | `rc:Dataset` is broad; tabular resources can also be `rc:Table`. |
| `mnf:SemanticType` | `rc:ValueType` | Domain-meaningful type of values. |
| `mnf:semanticType` | `rc:valueType` | Column to value-type link. |
| `mnf:groupSemanticType` | `rc:groupValueType` | Column-group to composite value-type link. |
| `mnf:SameEntity` | `rc:SharedIdentifier` | Avoids confusion with `owl:sameAs`. |
| `mnf:KnownDeficiency` | `rc:KnownCaveat` | Broader than outright deficiency. |
| `mnf:hasKnownDeficiency` | `rc:hasKnownCaveat` | Dataset/table to caveat link. |
| `mnf:deficiencyDescription` | `rc:caveatDescription` | Human-readable caveat text. |
| `mnf:violatedInvariant` | `rc:violatedExpectation` | Broader expectation/rule wording. |
| `mnf:AggregationRelationship` | `rc:Aggregation` | Shorter relationship class name. |

## Direct Carries

Many Manifest terms carry directly into `rc:` with the same local name:

- data structure: `hasColumn`, `Column`, `ColumnGroup`, `columnName`, `physicalType`, `nullable`
- value constraints: `requiredPhysicalType`, `valueRange`, `minInclusive`, `maxInclusive`, `minExclusive`, `maxExclusive`, `hasAllowedValues`, `allowedValue`
- row/schema modelling: `rowSemantics`, `EventRow`, `SnapshotRow`, `AggregateRow`, `entityKey`, `snapshotTimestamp`, `schemaStability`, `FixedSchema`, `InferredSchema`, `VariableSchema`
- layout: `PhysicalLayout`, `fileFormat`, `hasRowOrdering`, `OrderingKey`, `partitionedBy`, `PartitionScheme`, `CompositePartitionScheme`, `PartitionLevel`
- provenance: `Provenance`, `hasProvenance`, `source`, `sourceDescription`, `Transformation`, `hasTransformation`
- relationships: `ForeignKey`, `foreignKeyFrom`, `foreignKeyTo`, `referentialIntegrity`, `PartialIntegrity`, `identifyingColumn`

## Fixture Decisions

The fixtures do not put AIS or Polymarket domain concepts under `rc:`. They are client/project extensions on top of `rc:`.

The source Manifest descriptions do not contain fresh profiler output, so the `observations` graphs only record migration-time/source-scope observations. Real row counts, distinct counts, and value frequencies should be added as `rc:ProfileObservation` resources when produced by a profiler or agent run.
