/* Map view for frame-query results (doc 13 section 2 item 4, owner design
 * note 2026-07-21: "the map is a second renderer for query results, not a
 * geospatial subsystem"). Reads the JSON payload workbench/maps.py built
 * from the same (columns, rows) the results table renders, and draws it
 * with vendored Leaflet -- points, a color-by dropdown (categorical
 * palette or numeric gradient, per workbench's dataviz-skill palette
 * instance), and an optional "join as path" line.
 *
 * No build step, no framework: this is the one plain script the dataset
 * page loads when its frame schema has a recognizable coordinate pair.
 */
(function () {
  "use strict";

  // Same slot order as the reference categorical palette
  // (doxabase_design_docs' dataviz-skill instance) -- fixed order, never
  // cycled or reassigned per filter, per that skill's rule.
  var CATEGORICAL_COLORS = [
    "#2a78d6", "#1baf7a", "#eda100", "#008300",
    "#4a3aa7", "#e34948", "#e87ba4", "#eb6834",
  ];
  var OTHER_COLOR = "#898781"; // "other" bucket / muted ink, distinct from every categorical slot
  var NULL_COLOR = "#898781"; // missing color-by value on an otherwise-plottable point
  // 5-step sequential blue, light -> dark (palette steps 150/300/450/600/700).
  var SEQUENTIAL_COLORS = ["#b7d3f6", "#6da7ec", "#2a78d6", "#184f95", "#0d366b"];

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function round(n) {
    return typeof n === "number" ? Math.round(n * 10000) / 10000 : n;
  }

  function categoryColor(rank) {
    return rank < 0 ? OTHER_COLOR : CATEGORICAL_COLORS[rank % CATEGORICAL_COLORS.length];
  }

  function numericColor(meta, value) {
    var breaks = meta.breaks;
    for (var i = 0; i < 5; i++) {
      var atTop = i === 4;
      if (value >= breaks[i] && (atTop ? value <= breaks[i + 1] : value < breaks[i + 1])) {
        return SEQUENTIAL_COLORS[i];
      }
    }
    return value < breaks[0] ? SEQUENTIAL_COLORS[0] : SEQUENTIAL_COLORS[4];
  }

  function colorFor(meta, value) {
    if (!meta || value === null || value === undefined) return NULL_COLOR;
    if (meta.kind === "numeric") {
      return typeof value === "number" ? numericColor(meta, value) : NULL_COLOR;
    }
    return categoryColor(meta.categories.indexOf(String(value)));
  }

  function buildLegend(meta) {
    var el = document.createElement("div");
    if (!meta) {
      el.className = "map-legend-empty";
      el.textContent = "No color-by column selected -- every point is the default color.";
      return el;
    }
    var title = document.createElement("div");
    title.className = "map-legend-title";
    title.textContent = meta.name;
    el.appendChild(title);

    if (meta.kind === "categorical") {
      meta.categories.forEach(function (cat, i) {
        el.appendChild(legendRow(categoryColor(i), cat));
      });
      if (meta.has_other) {
        var extra = meta.total_categories - meta.categories.length;
        el.appendChild(legendRow(OTHER_COLOR, "other (" + extra + " more value(s))"));
      }
    } else {
      var bar = document.createElement("div");
      bar.className = "map-legend-gradient";
      SEQUENTIAL_COLORS.forEach(function (c) {
        var seg = document.createElement("span");
        seg.style.background = c;
        bar.appendChild(seg);
      });
      el.appendChild(bar);
      var ticks = document.createElement("div");
      ticks.className = "map-legend-ticks";
      meta.breaks.forEach(function (b) {
        var tick = document.createElement("span");
        tick.textContent = round(b);
        ticks.appendChild(tick);
      });
      el.appendChild(ticks);
    }
    return el;
  }

  function legendRow(color, label) {
    var row = document.createElement("div");
    row.className = "map-legend-row";
    var swatch = document.createElement("span");
    swatch.className = "map-swatch";
    swatch.style.background = color;
    row.appendChild(swatch);
    var text = document.createElement("span");
    text.textContent = label;
    row.appendChild(text);
    return row;
  }

  function popupHtml(payload, pt) {
    var rows = Object.keys(pt.fields).map(function (key) {
      return "<tr><th>" + escapeHtml(key) + "</th><td>" + escapeHtml(pt.fields[key]) + "</td></tr>";
    });
    rows.push("<tr><th>" + escapeHtml(payload.lat_col) + "</th><td>" + pt.lat + "</td></tr>");
    rows.push("<tr><th>" + escapeHtml(payload.lon_col) + "</th><td>" + pt.lon + "</td></tr>");
    return '<table class="map-popup">' + rows.join("") + "</table>";
  }

  function init() {
    var payloadEl = document.getElementById("map-payload");
    var canvas = document.getElementById("map-canvas");
    if (!payloadEl || !canvas) return;

    var payload = JSON.parse(payloadEl.textContent);
    if (!payload.points.length) {
      canvas.textContent = "No rows with both coordinate values to plot.";
      return;
    }

    var map = L.map(canvas, { scrollWheelZoom: true });
    if (canvas.dataset.tiles === "off") {
      canvas.classList.add("map-no-tiles");
    } else {
      // Tile URL/attribution come from the template (workbench/maps.py's
      // OSM_TILE_URL/OSM_ATTRIBUTION) rather than a second hardcoded copy
      // here.
      L.tileLayer(canvas.dataset.tileUrl, {
        attribution: canvas.dataset.attribution,
        maxZoom: 19,
      }).addTo(map);
    }

    var colorMetaByName = {};
    (payload.color_columns || []).forEach(function (c) { colorMetaByName[c.name] = c; });

    var bounds = L.latLngBounds([]);
    var markers = payload.points.map(function (pt) {
      var marker = L.circleMarker([pt.lat, pt.lon], {
        radius: 6, weight: 1, color: "#ffffff", fillOpacity: 0.85, fillColor: CATEGORICAL_COLORS[0],
      });
      marker.bindPopup(popupHtml(payload, pt));
      marker.addTo(map);
      bounds.extend([pt.lat, pt.lon]);
      return marker;
    });
    map.fitBounds(bounds.pad(0.15));

    var legendHost = document.getElementById("map-legend");
    function applyColor(colName) {
      var meta = colName ? colorMetaByName[colName] : null;
      markers.forEach(function (marker, i) {
        var value = colName ? payload.points[i].fields[colName] : null;
        marker.setStyle({ fillColor: colorFor(meta, value) });
      });
      legendHost.innerHTML = "";
      legendHost.appendChild(buildLegend(meta));
    }

    var colorSelect = document.getElementById("map-color-by");
    var colorControl = document.getElementById("map-color-control");
    if (payload.color_columns && payload.color_columns.length) {
      var noneOpt = document.createElement("option");
      noneOpt.value = "";
      noneOpt.textContent = "(none)";
      colorSelect.appendChild(noneOpt);
      payload.color_columns.forEach(function (c) {
        var opt = document.createElement("option");
        opt.value = c.name;
        opt.textContent = c.name + (c.kind === "numeric" ? " (numeric)" : " (categorical)");
        colorSelect.appendChild(opt);
      });
      colorSelect.value = payload.default_color || "";
      colorSelect.addEventListener("change", function () { applyColor(colorSelect.value); });
      applyColor(colorSelect.value);
    } else {
      if (colorControl) colorControl.hidden = true;
      applyColor(null);
    }

    var pathWrap = document.getElementById("map-path-toggle-wrap");
    var pathToggle = document.getElementById("map-path-toggle");
    if (payload.path_available) {
      pathWrap.hidden = false;
      document.getElementById("map-order-col").textContent = payload.order_col;
      var pathLine = null;
      pathToggle.addEventListener("change", function () {
        if (pathLine) { map.removeLayer(pathLine); pathLine = null; }
        if (pathToggle.checked) {
          var ordered = payload.points.slice().sort(function (a, b) {
            var av = a.fields[payload.order_col];
            var bv = b.fields[payload.order_col];
            return av < bv ? -1 : av > bv ? 1 : 0;
          });
          pathLine = L.polyline(
            ordered.map(function (p) { return [p.lat, p.lon]; }),
            { color: "#1a5276", weight: 2, opacity: 0.7 }
          ).addTo(map);
        }
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
