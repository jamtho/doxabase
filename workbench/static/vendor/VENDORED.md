# Vendored front-end libraries

## Leaflet 1.9.4

- Source: `https://registry.npmjs.org/leaflet/-/leaflet-1.9.4.tgz`
  (sha1 `23fae724e282fa25745aff82ca4d394748db7d8d`, matches the npm
  registry's published `dist.shasum` for this version — verified at
  vendor time).
- Files taken from the tarball's `package/dist/`: `leaflet.js`,
  `leaflet.css`, and `images/{layers,layers-2x,marker-icon,
  marker-icon-2x,marker-shadow}.png`. The unminified `leaflet-src.js`
  and both `.js.map` source maps were left out (dev-only, ~1MB extra);
  the trailing `//# sourceMappingURL=leaflet.js.map` comment was
  trimmed from `leaflet.js` since no map ships. No source was edited
  otherwise.
- License: BSD-2-Clause (see the header comment in `leaflet.js` and
  https://github.com/Leaflet/Leaflet/blob/main/LICENSE).
- Footprint: ~192KB total (leaflet.js ~144KB, leaflet.css ~14KB,
  marker/layer PNGs ~6.5KB) — the map panel's only front-end
  dependency.
- No CDN reference at runtime: the map template loads
  `/static/vendor/leaflet/leaflet.{js,css}` served by the workbench's
  own StaticFiles mount. The only runtime network calls Leaflet makes
  are OSM tile requests from the viewer's own browser (see
  `WORKBENCH_TILES` in the README) — the library itself is fully
  local.
- To upgrade: repeat the same npm-tarball download-and-verify, replace
  the three file groups above, and reread Leaflet's changelog for any
  removed API workbench/static/map.js depends on (`L.map`,
  `L.tileLayer`, `L.circleMarker`, `L.polyline`, `bindPopup`,
  `fitBounds`).
