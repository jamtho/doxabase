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
- `https://richcanopy.org/graph/evidence`

`DoxyBase.import_trig()` and the MCP import tools map those IRIs to local graph role names.

These fixtures are representative tests, not full mechanical conversions. They are useful for checking whether agents can discover tables, columns, value types, joins, caveats, and validation state.
