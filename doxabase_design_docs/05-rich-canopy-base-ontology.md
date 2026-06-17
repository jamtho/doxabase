# Rich Canopy Base Ontology for DoxaBase

## Purpose

DoxaBase should ship with a small Rich Canopy base ontology under the `rc:` prefix.

The base ontology is a helpful kernel for describing data projects, not a closed world and not a complete theory of data. Clients must be able to extend the graph in any direction that suits their project. DoxaBase should accept arbitrary parse-valid RDF, whether or not it uses `rc:` terms.

The base ontology gives agents shared handles for common data-modeling facts: data assets, tables, columns, semantic value types, joins, profile observations, known caveats, physical layout, and evidence. Clients get more built-in retrieval and validation help when they use these terms, but they are not forced to model everything this way.

## Design Posture

Use `rc:` for Rich Canopy vocabulary terms. DoxaBase is part of the Rich Canopy cluster, so there should not be a separate `doxa:` vocabulary for the client-facing data model in V1.

Reuse established RDF vocabularies when the cost is low:

- `rdf:` and `rdfs:` for core RDF structure, labels, comments, classes, and properties.
- `xsd:` for datatypes.
- `skos:` for value vocabularies and concept schemes.
- `dcterms:` for simple source/creator/time metadata where it fits.
- `owl:` for ontology identity and lightweight term deprecation/replacement metadata where it fits.
- `sh:` for SHACL shapes.

Avoid heavy dependency on large external ontologies in V1. In particular, do not require full PROV-O modelling for ordinary provenance. A lightweight `rc:Provenance`, `rc:Transformation`, and `rc:Evidence` pattern is enough for V1, with room to map to PROV-O later.

## Inspiration

The reference project is `../manifest-prototype`. Its Manifest vocabulary has the right broad shape but should be ported intentionally, not blindly renamed. DoxaBase should keep the useful modelling patterns and take the chance to improve names where helpful.

Patterns worth preserving:

- description and verification are decoupled
- structural enums use URI individuals instead of freeform string literals
- SHACL validates description graphs, not data files themselves
- known caveats are first-class graph resources
- observed/profiled facts can be represented separately from durable project-map conclusions
- generic structural terms compose with client-defined domain terms

The fixtures in `../examples/manifest-prototype-rc/` are representative ports of the reference project into `rc:` graph roles. They are test material for this base ontology, not a replacement for client-specific domain namespaces.

## Default Graph Placement

DoxaBase V1 should distinguish shipped immutable seed graphs from project-owned mutable graphs.

Shipped seed graphs:

```text
base_ontology
base_shapes
```

Project-owned graphs:

```text
map
ontology
observations
evidence
shapes
history
```

The shipped seed graphs are loaded from package Turtle files and should behave as immutable named graphs inside a memory capsule. The project-owned `ontology` and `shapes` graphs extend or refine by addition; they should not mutate the shipped base terms in place.

For retrieval ergonomics, APIs may expose logical include aliases:

- `ontology` means `base_ontology` plus project `ontology` unless the caller asks for physical graph names.
- `shapes` means `base_shapes` plus project `shapes` unless the caller asks for physical graph names.

V1 should reject ordinary graph revisions that target `base_ontology` or `base_shapes`.

### `base_ontology`

The immutable Rich Canopy vocabulary shipped with DoxaBase. In this repo, the starter file is `../ontology/rc_core.ttl` relative to this docs folder.

### `base_shapes`

The immutable SHACL shapes shipped with DoxaBase. In this repo, the starter file is `../ontology/rc_shapes.ttl` relative to this docs folder.

### `ontology`

The project-owned slower-changing vocabulary/model layer:

- client-defined classes and properties
- semantic/value types
- SKOS concepts and value vocabularies
- labels, comments, definitions
- domain/range-ish modelling
- term deprecations and replacements
- ontology-level relationships

### `map`

The current best structured map of the project/data world:

- data assets, datasets, databases, files, tables, columns
- mappings from columns to semantic/value types
- accepted joins and shared identifiers
- grain, row semantics, caveats, computability claims
- current profile summaries and links to supporting observations
- assertions about what the data means

### `observations`

Point-in-time or tentative findings:

- row-count/null-count/distinct-count discoveries
- observed values and value frequencies
- candidate joins
- failed assumptions
- ad hoc notes
- exploratory discoveries
- agent-run observations

Most isolated facts discovered during online work belong here. Offline consolidation can infer a more useful map assertion from many observations. For example, a sequence of contradictory profile observations may consolidate into a map-level caveat that the source is unstable, not into a single latest value.

### `evidence`

Support for observations or map assertions:

- SQL queries
- file paths or source URIs
- evidence summaries
- row samples
- content hashes
- validation reports

### `shapes`

SHACL shapes for `rc:` terms and client extensions. Shapes should be open and opt-in in V1. Do not use closed-world shapes that reject arbitrary client RDF.

### `history`

Graph versions, revisions, diffs, superseded terms, deprecated mappings, and consolidation rationale.

## Initial Term Families

The base ontology should start with term families, not an exhaustive catalogue. Clients can extend each family with their own classes and properties.

### Data Assets

Suggested starting classes:

```text
rc:DataAsset
rc:Dataset
rc:Database
rc:DataFile
rc:Table
rc:Column
rc:ColumnGroup
rc:DataFrame
```

`rc:DataAsset` is the broad root. `rc:Table` means a logical tabular structure with rows and columns. SQL tables, database views, Parquet files, CSV files, dataframes, and query results may all be `rc:Table` when appropriate. A single resource can have multiple types.

Examples:

```turtle
:orders_parquet a rc:DataFile, rc:Dataset, rc:Table .
:orders_view a rc:Table .
:warehouse a rc:Database, rc:DataAsset .
```

Leave room for future non-tabular assets such as JSON documents, unstructured text files, images, model artefacts, vector stores, APIs, streams, and document collections. V1 does not need to model all of them deeply.

Suggested starting properties:

```text
rc:hasColumn
rc:hasColumnGroup
rc:columnName
rc:groupValueType
rc:groupMember
rc:memberOf
rc:physicalType
rc:valueType
rc:nullable
rc:rowSemantics
rc:entityKey
rc:snapshotTimestamp
rc:schemaStability
rc:rowCountSnapshot
rc:pathTemplate
rc:hasStorageAccess
```

`rc:valueType` is the renamed equivalent of Manifest's `mnf:semanticType`: the domain-meaningful type of values in a column. Client projects can define any number of their own value types.

### Physical and Value Types

Suggested starting classes:

```text
rc:PhysicalType
rc:ValueType
rc:ValueRange
rc:AllowedValues
rc:EmbeddedStructure
```

Suggested starting properties:

```text
rc:requiredPhysicalType
rc:acceptablePhysicalType
rc:valueRange
rc:minInclusive
rc:maxInclusive
rc:minExclusive
rc:maxExclusive
rc:unit
rc:identifierNamespace
rc:hasAllowedValues
rc:allowedValue
rc:embeddedStructure
rc:embeddedFormat
rc:embeddedElementType
rc:caseConvention
```

Observed values and declared allowed values must remain distinct. Declared allowed values express a model or contract. Observed values express what an agent or profiler saw at a particular time, sample, or scope.

### Relationships

Suggested starting classes:

```text
rc:ForeignKey
rc:SharedIdentifier
rc:Aggregation
rc:AggregatedColumn
rc:Derivation
rc:DerivationProperty
```

`rc:SharedIdentifier` is the renamed equivalent of Manifest's `mnf:SameEntity`. It avoids confusion with `owl:sameAs`; it means multiple columns carry identifiers for the same logical entity or join population.

Suggested starting properties:

```text
rc:foreignKeyFrom
rc:foreignKeyTo
rc:referentialIntegrity
rc:declared
rc:identifyingColumn
rc:sourceDataset
rc:targetDataset
rc:sourceColumn
rc:targetColumn
rc:derivedColumn
rc:derivationFunction
rc:hasDerivationProperty
rc:hasAggregatedColumn
rc:aggregationSourceColumn
rc:aggregationFunction
rc:withinGroupOrdering
rc:companionOf
```

### Layout

Suggested starting classes:

```text
rc:PhysicalLayout
rc:FileFormat
rc:CompressionCodec
rc:RowOrdering
rc:OrderingKey
rc:PartitionScheme
rc:CompositePartitionScheme
rc:PartitionLevel
rc:StorageAccess
rc:StorageProtocol
rc:AccessMode
```

These terms are useful but should stay optional. Many assets have no known or meaningful ordering, no partition scheme, or no file-like layout.

Storage access terms describe non-secret execution context: protocol, storage
root, bucket/prefix, endpoint profile, path-style access, credential reference,
and intended access mode. They should help agents plan queries while keeping
actual secrets and user-specific runtime configuration outside the graph.

### Observations and Profiles

Suggested starting classes:

```text
rc:Observation
rc:ProfileObservation
rc:Evidence
rc:VerificationAttestation
```

Suggested starting properties:

```text
rc:observedAt
rc:observedBy
rc:observedAsset
rc:observedColumn
rc:sampleSize
rc:rowCount
rc:nullCount
rc:distinctCount
rc:observedValueFrequency
rc:observedValue
rc:valueFrequency
rc:evidence
rc:summary
```

Point-in-time facts should generally be observations. Consolidation can promote or interpret them into the `map` graph when useful.

Example:

```turtle
:profile_2026_05_30_status a rc:ProfileObservation ;
    rc:observedAt "2026-05-30T12:00:00Z"^^xsd:dateTime ;
    rc:observedColumn :orders_status ;
    rc:rowCount 1000 ;
    rc:nullCount 0 ;
    rc:distinctCount 2 ;
    rc:observedValueFrequency :profile_2026_05_30_status_open,
        :profile_2026_05_30_status_closed .

:profile_2026_05_30_status_open a rc:ObservedValueFrequency ;
    rc:observedValue "open" ;
    rc:valueFrequency 740 .

:profile_2026_05_30_status_closed a rc:ObservedValueFrequency ;
    rc:observedValue "closed" ;
    rc:valueFrequency 260 .
```

### Caveats

Suggested starting classes:

```text
rc:KnownCaveat
rc:Constraint
```

`rc:KnownCaveat` is the renamed broader form of Manifest's `mnf:KnownDeficiency`. It covers actual deficiencies, caveats, unstable assumptions, broken joins, non-obvious interpretation rules, and other things consumers should not silently assume away.

Suggested starting properties:

```text
rc:hasKnownCaveat
rc:caveatDescription
rc:violatedExpectation
rc:impact
rc:severity
```

## SHACL Posture

V1 shapes should validate well-formed use of `rc:` terms, not every RDF statement in the capsule.

Guidelines:

- keep shapes open; avoid `sh:closed true` in V1
- target explicit `rc:` classes
- validate simple cardinality, datatype, node-kind, and enum constraints
- document conditional expectations instead of reaching for SPARQL-based SHACL unless a strong use case appears
- allow client-defined classes/properties to coexist without validation failure

This matches DoxaBase's product posture: parse-valid RDF is mandatory, SHACL is an explicit diagnostic operation, and agents/clients retain freedom to evolve their model.

## V1 Deliverable

The immediate V1 design deliverable is this vocabulary direction, the graph-placement contract, and starter Turtle seed files:

- `../ontology/rc_core.ttl`: immutable base `rc:` vocabulary for `base_ontology`.
- `../ontology/rc_shapes.ttl`: immutable open SHACL shapes for `base_shapes`.
- `../examples/manifest-prototype-rc/`: representative AIS and Polymarket ports used to test the base ontology against real modelling pressure.

These files are draft seed material. Project-specific ontology terms and SHACL shapes should still live in mutable project graphs.
