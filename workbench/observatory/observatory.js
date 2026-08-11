/* DoxaBase Capsule Observatory -- static viewer (doc 11 section 2).
 *
 * No build step, no framework -- the same house style as
 * workbench/static/map.js. Loads manifest.json, then each layer's
 * layers/*.geojson, renders them with Leaflet (vendored, matching the
 * workbench's own choice), and opens a "how this is known" panel for
 * every clicked feature by lazily fetching provenance/<feature id>.json
 * (doc 11 section 1: that panel is the product).
 *
 * Rendering rules honored (round-4/5/6 expert observations in the AIS
 * capsule, doc 11 section 4/7):
 *   - lead with what's being shown: the header states mode, data window,
 *     and export-eligibility status before anything else loads.
 *   - joined motion: any feature with 2+ points renders as a line with
 *     markers at each vertex, not disconnected dots.
 *   - folders by classification: story features group by their aisv:
 *     type, shuttle-census features group by AIS vessel class, and the
 *     17-vessel "stopped" sub-population gets its own always-visible
 *     highlight group.
 *   - a line between two features always states its relationship type in
 *     its own popup/detail text; this viewer never draws proximity as
 *     implication (doc 11 section 1's anti-insinuation rule) -- the only
 *     lines drawn are a single feature's own recorded path (an exit/
 *     return silence event, or one vessel's two dwell poles), never a
 *     line invented between two different resources.
 *
 * Two owner asks added after the layers-1-2 MVP:
 *   - optional vessel tracks (layers/tracks.geojson, kind "context" in
 *     the manifest): each story-map vessel's full, thinned broadcast
 *     track, rendered in a dedicated low-z-index Leaflet pane so it
 *     always sits beneath the story/shuttle features regardless of
 *     fetch/add order -- "the eye reads joined motion; points of
 *     interest need the track for context" (round-5). Muted color, no
 *     per-vertex markers (would be noise at thousands of points), no
 *     click-through provenance panel (raw broadcast fixes, not a graph
 *     claim) -- just a popup with the thinning stats. Toggleable
 *     per-vessel via the same layers control, initially on.
 *   - a second base layer (Esri World Imagery) alongside OSM streets,
 *     reusing workbench/maps.py's tile URL/attribution constants via
 *     manifest.tiles.basemaps -- the same two-basemap switcher the
 *     workbench's own map panel (static/map.js) already has.
 */
(function () {
  "use strict";

  var CATEGORICAL_COLORS = [
    "#2a78d6", "#1baf7a", "#eda100", "#008300",
    "#4a3aa7", "#e34948", "#e87ba4", "#eb6834",
  ];
  var STOPPED_COLOR = "#e34948";
  var MUTED_COLOR = "#898781";

  var STORY_TYPE_META = {
    silence_period: { label: "Silence periods", colorIndex: 0 },
    dwell_period: { label: "Dwell periods", colorIndex: 1 },
    identity_change: { label: "Identity changes", colorIndex: 2 },
    draft_change_event: { label: "Draft-change events", colorIndex: 3 },
  };

  var VESSEL_CLASS_META = {
    cargo: { label: "Cargo", colorIndex: 0 },
    tanker: { label: "Tanker", colorIndex: 1 },
    passenger: { label: "Passenger", colorIndex: 2 },
    pleasure_sailing: { label: "Pleasure / sailing", colorIndex: 3 },
    fishing: { label: "Fishing", colorIndex: 4 },
    towing: { label: "Towing", colorIndex: 5 },
    specialized_service: { label: "Specialized service", colorIndex: 6 },
    high_speed_craft: { label: "High-speed craft", colorIndex: 7 },
    dredging: { label: "Dredging", colorIndex: 0 },
    diving_military: { label: "Diving / military", colorIndex: 1 },
    other: { label: "Other", colorIndex: 2 },
    unknown: { label: "Unclassified", colorIndex: 3 },
  };

  function colorForIndex(i) {
    return CATEGORICAL_COLORS[i % CATEGORICAL_COLORS.length];
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function fmt(value, fallback) {
    if (value === null || value === undefined || value === "") return fallback || "—";
    return escapeHtml(value);
  }

  function fetchJson(url) {
    return fetch(url).then(function (resp) {
      if (!resp.ok) throw new Error(url + " -> HTTP " + resp.status);
      return resp.json();
    });
  }

  // ---------------------------------------------------------------
  // Detail panel ("how this is known")

  var detailEmpty = document.getElementById("detail-empty");
  var detailContent = document.getElementById("detail-content");

  function showDetailLoading(title) {
    detailEmpty.hidden = true;
    detailContent.hidden = false;
    detailContent.innerHTML =
      "<h2>" + escapeHtml(title) + "</h2><p>Loading provenance…</p>";
  }

  function showDetailError(title, err) {
    detailContent.innerHTML =
      "<h2>" + escapeHtml(title) + "</h2><p>Could not load provenance: " +
      escapeHtml(err.message || err) +
      "</p><p class=\"iri\">If you opened this file directly (file://), " +
      "most browsers block fetching adjacent JSON. Serve the bundle with " +
      "a local static server instead, e.g. <code>python -m http.server</code> " +
      "from inside the bundle directory.</p>";
  }

  function renderClaimChainHtml(chain) {
    if (!chain || !chain.length) {
      return "<p class=\"iri\">No claim recorded for this resource.</p>";
    }
    return chain
      .map(function (claim) {
        var html = "<div class=\"chain-step\">";
        html += "<div><span class=\"confidence\">" + fmt(claim.confidence) + "</span> ";
        html += fmt(claim.claim_kind) + "</div>";
        html += "<p>" + fmt(claim.claim_text) + "</p>";
        html += "<div class=\"iri\">claim: " + fmt(claim.claim_iri) + "</div>";
        (claim.observations || []).forEach(function (obs) {
          html += "<div class=\"chain-step\">";
          html += "<p>" + fmt(obs.summary) + "</p>";
          html += "<div class=\"iri\">observation: " + fmt(obs.iri) + "</div>";
          if (obs.observed_at) {
            html += "<div class=\"iri\">observed at: " + fmt(obs.observed_at) + "</div>";
          }
          (obs.evidence || []).forEach(function (ev) {
            html += "<div class=\"chain-step\">";
            html += "<p>" + fmt(ev.summary) + "</p>";
            if (ev.source && ev.source.length) {
              html += "<div class=\"iri\">source: " + fmt(ev.source.join(", ")) + "</div>";
            }
            html += "<div class=\"iri\">evidence: " + fmt(ev.iri) + "</div>";
            html += "</div>";
          });
          html += "</div>";
        });
        html += "</div>";
        return html;
      })
      .join("");
  }

  function renderStoryDetail(props, provenance) {
    var html = "<h2>" + fmt(props.label, props.id) + "</h2>";
    html += "<div class=\"field\"><dt>Type</dt><dd>" + fmt(props.story_type) + "</dd></div>";
    if (props.vessel_label) {
      html += "<div class=\"field\"><dt>Vessel</dt><dd>" + fmt(props.vessel_label) + "</dd></div>";
    }
    if (props.summary) {
      html += "<div class=\"field\"><dt>Story summary</dt><dd class=\"summary\">" +
        fmt(props.summary) + "</dd></div>";
    }
    html += "<div class=\"field\"><dt>Place (as recorded)</dt><dd>" + fmt(props.place_text) + "</dd></div>";
    html += "<div class=\"field\"><dt>Resource IRI</dt><dd class=\"iri\">" + fmt(props.iri) + "</dd></div>";
    html += "<div class=\"provenance-block\"><h3>How this is known</h3>" +
      renderClaimChainHtml(provenance.claim_chain) + "</div>";
    detailContent.innerHTML = html;
  }

  function renderShuttleDetail(props, provenance) {
    var html = "<h2>MMSI " + fmt(props.mmsi) + (props.vessel_name ? " — " + fmt(props.vessel_name) : "") + "</h2>";
    html += "<div class=\"field\"><dt>Vessel class</dt><dd>" + fmt(props.vessel_class) +
      " (AIS type " + fmt(props.ais_type, "unknown") + ")</dd></div>";
    html += "<div class=\"field\"><dt>Emitter class (M2)</dt><dd>" + fmt(props.emitter_class) + "</dd></div>";
    if (props.stopped) {
      html += "<div class=\"field\"><dt>Stopped (last active before 2025-06-01)</dt><dd>" +
        fmt(props.stop_kind) + " — " + fmt(props.stop_note) + "</dd></div>";
    }
    html += "<div class=\"field\"><dt>Two-pole metrics</dt><dd>" +
      "concentration " + fmt(props.concentration) +
      ", spans at poles " + fmt(props.n_spans_top2) +
      ", pole switches " + fmt(props.n_switches) +
      ", dwell fraction " + fmt(props.dwell_fraction) +
      ", window " + fmt(props.top2_window_days) + " days</dd></div>";
    html += "<div class=\"field\"><dt>Pole dwell-days</dt><dd>pole 1: " + fmt(props.pole1_days) +
      " days, pole 2: " + fmt(props.pole2_days) + " days</dd></div>";
    var chain = provenance.method_chain || [];
    var methodHtml = chain
      .map(function (step) {
        return "<div class=\"chain-step\"><div>" + fmt(step.role) + "</div>" +
          "<p>" + fmt(step.label) + "</p><div class=\"iri\">" + fmt(step.iri) + "</div></div>";
      })
      .join("");
    if (provenance.stop_classification) {
      var sc = provenance.stop_classification;
      methodHtml += "<div class=\"chain-step\"><div>stop classification (session 9)</div>" +
        "<p>" + fmt(sc.stop_kind) + ": " + fmt(sc.note) + "</p>" +
        "<div class=\"iri\">claim: " + fmt(sc.claim_iri) + "</div>" +
        "<div class=\"iri\">evidence: " + fmt(sc.evidence_iri) + "</div></div>";
    }
    html += "<div class=\"provenance-block\"><h3>How this is known</h3>" + methodHtml +
      "<p class=\"iri\">" + fmt(provenance.computation_note) + "</p></div>";
    detailContent.innerHTML = html;
  }

  function bindDetail(layer, feature) {
    layer.on("click", function () {
      var props = feature.properties;
      var title = props.layer === "story-map" ? (props.label || props.id) : "MMSI " + props.mmsi;
      showDetailLoading(title);
      fetchJson(props.provenance_ref)
        .then(function (provenance) {
          if (props.layer === "story-map") {
            renderStoryDetail(props, provenance);
          } else {
            renderShuttleDetail(props, provenance);
          }
        })
        .catch(function (err) {
          showDetailError(title, err);
        });
    });
  }

  // ---------------------------------------------------------------
  // Feature -> Leaflet layer (points render as circle markers; 2+ point
  // paths render as a joined line plus vertex markers -- "joined motion",
  // round-5's squiggle-reading lesson)

  function popupHtml(feature) {
    var props = feature.properties;
    if (props.layer === "story-map") {
      return "<b>" + fmt(props.label, props.id) + "</b>" + fmt(props.summary, "");
    }
    return "<b>MMSI " + fmt(props.mmsi) + (props.vessel_name ? " — " + fmt(props.vessel_name) : "") +
      "</b>" + fmt(props.vessel_class) + (props.stopped ? " (stopped)" : "");
  }

  function featureToLayers(feature, color, weight, radius) {
    var geom = feature.geometry;
    var layers = [];
    if (geom.type === "Point") {
      var latlng = [geom.coordinates[1], geom.coordinates[0]];
      layers.push(L.circleMarker(latlng, { radius: radius, color: color, weight: 2, fillOpacity: 0.85 }));
    } else if (geom.type === "LineString") {
      var latlngs = geom.coordinates.map(function (c) { return [c[1], c[0]]; });
      layers.push(L.polyline(latlngs, { color: color, weight: weight, opacity: 0.85 }));
      latlngs.forEach(function (ll) {
        layers.push(L.circleMarker(ll, { radius: radius * 0.7, color: color, weight: 2, fillOpacity: 0.9 }));
      });
    }
    layers.forEach(function (layer) {
      layer.bindPopup(popupHtml(feature));
      bindDetail(layer, feature);
    });
    return layers;
  }

  // ---------------------------------------------------------------
  // Vessel tracks (context layer): plain muted lines, no vertex markers
  // (a thinned track can still carry thousands of points -- markers at
  // every one would be visual noise, not context) and no click-through
  // provenance fetch (raw broadcast fixes are not a graph claim; a
  // popup with the thinning stats is enough).

  function trackPopupHtml(props) {
    var label = props.vessel_label ? fmt(props.vessel_label) : "MMSI " + fmt(props.mmsi);
    var html = "<b>" + label + " -- full track (context)</b>";
    html += "<div>" + fmt(props.rendered_point_count) + " of " + fmt(props.raw_point_count) +
      " broadcast fixes shown (every " + fmt(props.thinning_stride) + "-fix)</div>";
    if (props.segment_count > 1) {
      html += "<div>" + fmt(props.segment_count) + " segments, split wherever consecutive " +
        "fixes are more than " + fmt(props.silence_gap_minutes) + " minutes apart</div>";
    }
    html += "<div>" + fmt(props.first_fix_at) + " → " + fmt(props.last_fix_at) + "</div>";
    return html;
  }

  function trackFeatureToLayers(feature) {
    var geom = feature.geometry;
    var lineStrings = geom.type === "MultiLineString" ? geom.coordinates : [geom.coordinates];
    var popup = trackPopupHtml(feature.properties);
    return lineStrings.map(function (coords) {
      var latlngs = coords.map(function (c) { return [c[1], c[0]]; });
      var line = L.polyline(latlngs, {
        pane: "tracksPane", color: MUTED_COLOR, weight: 2, opacity: 0.55,
      });
      line.bindPopup(popup);
      return line;
    });
  }

  function buildTrackOverlays(geojson) {
    var overlays = {};
    geojson.features.forEach(function (feature) {
      var props = feature.properties;
      var group = L.layerGroup();
      trackFeatureToLayers(feature).forEach(function (l) { l.addTo(group); });
      var label = props.vessel_label ? props.vessel_label + " (MMSI " + props.mmsi + ")" : "MMSI " + props.mmsi;
      overlays["Vessel track — " + label + " (" + props.rendered_point_count + " pts)"] = group;
    });
    return overlays;
  }

  // ---------------------------------------------------------------
  // Layer building

  function buildStoryOverlays(geojson) {
    var groups = {};
    geojson.features.forEach(function (feature) {
      var storyType = feature.properties.story_type;
      var meta = STORY_TYPE_META[storyType] || { label: storyType, colorIndex: 7 };
      var color = colorForIndex(meta.colorIndex);
      var group = groups[storyType] || (groups[storyType] = { meta: meta, layer: L.layerGroup(), count: 0 });
      featureToLayers(feature, color, 4, 6).forEach(function (l) { l.addTo(group.layer); });
      group.count += 1;
    });
    var overlays = {};
    Object.keys(groups).forEach(function (storyType) {
      var g = groups[storyType];
      overlays["Story map — " + g.meta.label + " (" + g.count + ")"] = g.layer;
    });
    return overlays;
  }

  function buildShuttleOverlays(geojson) {
    var byClass = {};
    var stoppedGroup = L.layerGroup();
    var stoppedCount = 0;
    geojson.features.forEach(function (feature) {
      var props = feature.properties;
      var meta = VESSEL_CLASS_META[props.vessel_class] || { label: props.vessel_class, colorIndex: 7 };
      var color = colorForIndex(meta.colorIndex);
      var group = byClass[props.vessel_class] || (byClass[props.vessel_class] = { meta: meta, layer: L.layerGroup(), count: 0 });
      featureToLayers(feature, color, 3, 5).forEach(function (l) { l.addTo(group.layer); });
      group.count += 1;
      if (props.stopped) {
        featureToLayers(feature, STOPPED_COLOR, 5, 7).forEach(function (l) { l.addTo(stoppedGroup); });
        stoppedCount += 1;
      }
    });
    var overlays = {};
    Object.keys(byClass).forEach(function (vesselClass) {
      var g = byClass[vesselClass];
      overlays["Shuttle census — " + g.meta.label + " (" + g.count + ")"] = g.layer;
    });
    if (stoppedCount) {
      overlays["Shuttle census — stopped, last active before 2025-06-01 (" + stoppedCount + ")"] = stoppedGroup;
    }
    return overlays;
  }

  // ---------------------------------------------------------------
  // Header / footer

  function renderHeader(manifest) {
    var meta = document.getElementById("header-meta");
    var eligibility = manifest.export_eligibility || {};
    var pieces = [];
    pieces.push('<span class="pill">' + fmt(manifest.mode) + " mode</span>");
    pieces.push('<span class="pill pending-review">' + fmt(eligibility.status) + "</span>");
    if (manifest.capsule && manifest.capsule.data_window) {
      pieces.push('<span class="pill">data window: ' + fmt(manifest.capsule.data_window) + "</span>");
    }
    pieces.push('<span class="pill">generated ' + fmt(manifest.generated_at) + "</span>");
    meta.innerHTML = pieces.join("");

    var footer = document.getElementById("app-footer");
    footer.innerHTML = fmt(eligibility.note, "");
  }

  // ---------------------------------------------------------------
  // Boot

  fetchJson("manifest.json")
    .then(function (manifest) {
      renderHeader(manifest);

      var tilesEnabled = manifest.tiles && manifest.tiles.enabled;
      var mapEl = document.getElementById("map");
      if (!tilesEnabled) mapEl.className = "no-tiles";

      var map = L.map("map", { worldCopyJump: true }).setView([30, -85], 4);

      // Below the default overlayPane (z-index 400) so vessel tracks always
      // render beneath story-map/shuttle-census features regardless of which
      // layer's async fetch happens to resolve/add first (doc 11 round-5:
      // tracks are context for the points of interest, not the other way
      // round). Still above the tile pane (200) so it's visible over the base.
      map.createPane("tracksPane");
      map.getPane("tracksPane").style.zIndex = 350;

      var baseLayers = {};
      if (tilesEnabled) {
        // manifest.tiles.basemaps: the full switchable set (owner ask --
        // Esri World Imagery alongside OSM streets, workbench/maps.py's own
        // tile URL/attribution constants, reused not re-hardcoded). Falls
        // back to the single top-level url/attribution for older bundles.
        var basemaps = (manifest.tiles.basemaps && manifest.tiles.basemaps.length)
          ? manifest.tiles.basemaps
          : [{ id: "default", label: "Base map", url: manifest.tiles.url, attribution: manifest.tiles.attribution }];
        basemaps.forEach(function (bm, i) {
          var layer = L.tileLayer(bm.url, { attribution: bm.attribution, maxZoom: 19 });
          baseLayers[bm.label] = layer;
          if (i === 0) layer.addTo(map);
        });
      }

      var layerFiles = manifest.layers.map(function (layer) { return fetchJson(layer.file).then(function (geojson) {
        return { layer: layer, geojson: geojson };
      }); });

      Promise.all(layerFiles).then(function (loaded) {
        var overlays = {};
        var allBoundsLayers = [];
        loaded.forEach(function (entry) {
          var built;
          if (entry.layer.id === "story-map") {
            built = buildStoryOverlays(entry.geojson);
          } else if (entry.layer.id === "tracks") {
            built = buildTrackOverlays(entry.geojson);
          } else {
            built = buildShuttleOverlays(entry.geojson);
          }
          var isTracks = entry.layer.id === "tracks";
          Object.keys(built).forEach(function (name) {
            overlays[name] = built[name];
            built[name].addTo(map);
            // Tracks are context, not the primary content -- initial fitBounds
            // stays driven by the story/shuttle features so a sprawling
            // 2-year vessel track doesn't zoom the opening view out past them.
            if (!isTracks) allBoundsLayers.push(built[name]);
          });
        });
        L.control.layers(baseLayers, overlays, { collapsed: false }).addTo(map);

        var group = L.featureGroup(allBoundsLayers.reduce(function (acc, lg) {
          lg.eachLayer(function (l) { acc.push(l); });
          return acc;
        }, []));
        if (group.getLayers().length) {
          map.fitBounds(group.getBounds().pad(0.1));
        }
      });
    })
    .catch(function (err) {
      document.getElementById("header-meta").textContent = "Failed to load manifest.json: " + err.message;
    });
})();
