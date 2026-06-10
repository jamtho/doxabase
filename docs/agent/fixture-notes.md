# Fixture Notes

The `examples/manifest-prototype-rc/` directory contains representative ports from `../manifest-prototype` into the `rc:` ontology.

Files:

- `ais.trig`
- `polymarket.trig`
- `mnf-to-rc-mapping.md`

The fixtures use named graph IRIs under:

```text
https://richcanopy.org/graph/
```

For example:

- `https://richcanopy.org/graph/ontology`
- `https://richcanopy.org/graph/map`
- `https://richcanopy.org/graph/observations`
- `https://richcanopy.org/graph/patterns`
- `https://richcanopy.org/graph/evidence`

`DoxaBase.import_trig()` and the MCP import tools map those IRIs to local graph role names.

These fixtures are representative tests, not full mechanical conversions. They are useful for checking whether agents can discover tables, columns, value types, joins, caveats, physical layout, storage access, and validation state.

The AIS fixture is intentionally reduced. It includes representative non-secret storage access metadata, but it does not currently represent the full real AIS broadcast or daily-index Parquet schemas. In particular, the real data includes vessel identity columns that are not present in the fixture.

The AIS `DailyIndex` fixture currently shares the broadcast partition path
pattern. The graph records this as `rc:UnverifiedLayout` on `ais:DailyIndex`,
and the shared partition template is marked
`rc:GeneratedFromManifestLayout`. The real daily index layout may use a
distinct `index/{year}/...` prefix, so agents should read
`layout_verification_status` / `layout_verification_note` and verify physical
layout metadata before generating executable queries.
