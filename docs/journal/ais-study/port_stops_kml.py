"""Build port-stops-map.kml: M11 berth/anchor classification at one port.

Expert round-5 feedback (map information design) drives the shape here:
lead with what we're trying to SHOW, join motion points with line segments,
label points with context, and for a classifier demo use ONE port with many
discovered anchor/berth stops in separate toggleable folders so the expert
can see where the classification falls and where it doesn't.

Port: San Diego Bay + its outer/border anchorage -- the busiest port region
in the M11 session-12 survey sample (work/m11_survey.parquet), 136 windows.

Decision rule (pattern 2fb8d9b7, confirmed via bridge):
  radius_mean_m < 20  & hollow_frac > 0.85  -> berth
  radius_mean_m > 50  & hollow_frac < 0.70  -> anchor
  else                                      -> ambiguous

Motion exhibit: ARMADA 78 07 (mmsi 563199100), 2024-02-20, one vessel-day of
broadcast fixes showing the transit from the outer anchorage (status=1 the
day before) to a San Diego Bay berth (status=5 by 03:29 UTC that day).

Usage: venv/bin/python port_stops_kml.py OUT.kml
S3 credentials come from the environment; never copied anywhere.
"""
import html
import os
import sys

import duckdb

OUT = sys.argv[1] if len(sys.argv) > 1 else "port-stops-map.kml"

# San Diego Bay + outer/border anchorage bounding box (see JOURNAL note: this
# is the port region with the most windows in the M11 survey sample).
LAT0, LAT1 = 32.30, 32.90
LON0, LON1 = -117.30, -117.02

# Motion exhibit: one vessel-day arrival, anchor area -> berth.
ARRIVAL_MMSI = 563199100
ARRIVAL_DATE = "2024-02-20"
ARRIVAL_NAME = "ARMADA 78 07"

STYLES = """
<Style id="berth"><IconStyle><color>ff00cc00</color><scale>0.7</scale>
<Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
</IconStyle><LabelStyle><scale>0.7</scale></LabelStyle></Style>
<Style id="anchor"><IconStyle><color>ff0088ff</color><scale>0.9</scale>
<Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
</IconStyle><LabelStyle><scale>0.7</scale></LabelStyle></Style>
<Style id="ambiguous"><IconStyle><color>ff888888</color><scale>0.6</scale>
<Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
</IconStyle><LabelStyle><scale>0.6</scale></LabelStyle></Style>
<Style id="arrivalTrack"><LineStyle><color>ffff3355</color><width>3</width></LineStyle></Style>
<Style id="arrivalFix"><IconStyle><color>ffff3355</color><scale>0.35</scale>
<Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
</IconStyle><LabelStyle><scale>0</scale></LabelStyle></Style>
<Style id="arrivalEnd"><IconStyle><color>ffffffff</color><scale>1.0</scale>
<Icon><href>http://maps.google.com/mapfiles/kml/paddle/wht-stars.png</href></Icon>
</IconStyle><LabelStyle><scale>0.8</scale></LabelStyle></Style>
"""


def connect():
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    endpoint = os.environ["MINIO_ENDPOINT"].replace("http://", "").replace("https://", "")
    con.execute(f"SET s3_endpoint='{endpoint}'")
    con.execute("SET s3_url_style='path'; SET s3_use_ssl=false; SET s3_region='local';")
    con.execute(f"SET s3_access_key_id='{os.environ['MINIO_ACCESS_KEY']}'")
    con.execute(f"SET s3_secret_access_key='{os.environ['MINIO_SECRET_KEY']}'")
    return con


def classify(radius_mean_m, hollow_frac):
    if radius_mean_m is not None and hollow_frac is not None:
        if radius_mean_m < 20 and hollow_frac > 0.85:
            return "berth"
        if radius_mean_m > 50 and hollow_frac < 0.70:
            return "anchor"
    return "ambiguous"


def load_stops(con):
    q = f"""
        SELECT s.mmsi, s.date, s.vessel_class, s.day_state, s.duration_hours,
               s.n_points, s.radius_mean_m, s.radius_median_m, s.hollow_frac,
               s.heading_R, s.heading_circular_sd_deg, s.frac_moored,
               s.frac_anchored, s.frac_underway0, s.position_quality_suspect,
               w.centroid_lat, w.centroid_lon, i.vessel_name_mode
        FROM read_parquet('work/m11_survey.parquet') s
        JOIN read_parquet('work/m11_sample_windows.parquet') w USING (mmsi, date)
        LEFT JOIN read_parquet('work/identity.parquet') i USING (mmsi)
        WHERE w.centroid_lat BETWEEN {LAT0} AND {LAT1}
          AND w.centroid_lon BETWEEN {LON0} AND {LON1}
        ORDER BY s.date, s.mmsi
    """
    return con.execute(q).fetchall()


def stop_placemark(row):
    (mmsi, date, vessel_class, day_state, duration_hours, n_points,
     radius_mean_m, radius_median_m, hollow_frac, heading_R,
     heading_circular_sd_deg, frac_moored, frac_anchored, frac_underway0,
     position_quality_suspect, lat, lon, vessel_name) = row
    cls = classify(radius_mean_m, hollow_frac)
    name = f"{vessel_name} - {duration_hours:.1f}h - r={radius_mean_m:.0f}m"
    agree = "AGREES" if (
        (cls == "berth" and day_state == "berthed")
        or (cls == "anchor" and day_state == "anchored")
    ) else ("N/A (self-report unclassified)" if day_state == "stationary_unclassified"
             else "DISAGREES")
    if heading_R is not None:
        heading_line = f"heading_R={heading_R:.3f}"
        if heading_circular_sd_deg is not None:
            heading_line += f"  circular_sd={heading_circular_sd_deg:.1f} deg"
    else:
        heading_line = "heading_R=n/a (no valid heading fixes in window)"
    desc_lines = [
        f"mmsi {mmsi} | {vessel_class} | {date}",
        f"M11 classification: {cls.upper()}  |  self-reported day_state: {day_state}  ({agree})",
        f"radius_mean_m={radius_mean_m:.1f}  radius_median_m={radius_median_m:.1f}  hollow_frac={hollow_frac:.3f}",
        heading_line,
        f"n_points={n_points}  duration_hours={duration_hours:.2f}",
        f"frac_moored={frac_moored:.2f}  frac_anchored={frac_anchored:.2f}  frac_underway0={frac_underway0:.2f}",
        f"position_quality_suspect={position_quality_suspect}",
    ]
    desc = html.escape("\n".join(desc_lines))
    return cls, (
        f"<Placemark><name>{html.escape(name)}</name>"
        f"<styleUrl>#{cls}</styleUrl>"
        f"<description><![CDATA[{desc.replace(chr(10), '<br/>')}]]></description>"
        f"<Point><coordinates>{lon:.6f},{lat:.6f},0</coordinates></Point></Placemark>"
    )


def build_stop_folders(con):
    rows = load_stops(con)
    buckets = {"berth": [], "anchor": [], "ambiguous": []}
    for row in rows:
        cls, placemark = stop_placemark(row)
        buckets[cls].append(placemark)
    folder_meta = [
        ("berth", "Berth stops (classified)", "green"),
        ("anchor", "Anchor stops (classified)", "orange"),
        ("ambiguous", "Ambiguous", "grey"),
    ]
    folders = []
    for key, label, _color in folder_meta:
        marks = "".join(buckets[key])
        folders.append(
            f"<Folder><name>{html.escape(label)} ({len(buckets[key])})</name>"
            f"<open>{'1' if key != 'ambiguous' else '0'}</open>{marks}</Folder>"
        )
    return folders, {k: len(v) for k, v in buckets.items()}, len(rows)


def build_arrival_exhibit(con):
    q = f"""
        SELECT base_date_time, latitude, longitude, sog, status
        FROM read_parquet('s3://ais-noaa/broadcasts/2024/ais-{ARRIVAL_DATE}.parquet')
        WHERE mmsi = {ARRIVAL_MMSI} AND latitude IS NOT NULL
        ORDER BY base_date_time
    """
    rows = con.execute(q).fetchall()

    coords = " ".join(f"{lon:.6f},{lat:.6f},0" for _, lat, lon, _, _ in rows)
    line = (
        f"<Placemark><name>{html.escape(ARRIVAL_NAME)} track ({ARRIVAL_DATE})</name>"
        f"<styleUrl>#arrivalTrack</styleUrl>"
        f"<LineString><tessellate>1</tessellate><coordinates>{coords}</coordinates></LineString>"
        "</Placemark>"
    )

    # Fix points: full resolution while underway (the interesting squiggle),
    # thinned once moored at berth (avoid stacking hundreds of identical
    # icons on one spot) -- still one placemark per joined-points principle,
    # with start/end called out.
    fix_marks = []
    moored_seen = 0
    for idx, (ts, lat, lon, sog, status) in enumerate(rows):
        first = idx == 0
        last = idx == len(rows) - 1
        if status == 5:  # moored
            moored_seen += 1
            keep = first or last or (moored_seen % 15 == 0)
        else:
            keep = True
        if not keep:
            continue
        style = "arrivalEnd" if (first or last) else "arrivalFix"
        label = ""
        if first:
            label = f"<name>{html.escape(ARRIVAL_NAME)} - departs outer anchorage</name>"
        elif last:
            label = f"<name>{html.escape(ARRIVAL_NAME)} - moored, end of day</name>"
        desc = html.escape(f"{ts}  sog={sog}  status={status}")
        fix_marks.append(
            f"<Placemark>{label}<styleUrl>#{style}</styleUrl>"
            f"<description>{desc}</description>"
            f"<Point><coordinates>{lon:.6f},{lat:.6f},0</coordinates></Point></Placemark>"
        )

    folder_desc = html.escape(
        f"{ARRIVAL_NAME} (mmsi {ARRIVAL_MMSI}), {ARRIVAL_DATE}: joined-points arrival exhibit. "
        f"Anchored (status=1) at the outer/border anchorage (~32.358,-117.108) through "
        f"the prior day; underway from 00:00 UTC; moored (status=5) in San Diego Bay "
        f"(~32.696,-117.154) by 03:29 UTC and stays put the rest of the day. "
        f"{len(rows)} broadcast fixes; line shows the full path, points are full-resolution "
        f"in transit and thinned once moored."
    )
    body = line + "".join(fix_marks)
    return (
        f"<Folder><name>Arrival exhibit: anchor to berth ({ARRIVAL_DATE})</name>"
        f"<open>1</open><description>{folder_desc}</description>{body}</Folder>"
    ), len(rows)


def main():
    con = connect()
    stop_folders, counts, total = build_stop_folders(con)
    arrival_folder, n_fixes = build_arrival_exhibit(con)

    doc_desc = html.escape(
        "M11's radius/hollow-fraction decision rule (pattern 2fb8d9b7) applied to "
        f"{total} stationary-window survey stops in the San Diego Bay + outer-anchorage "
        "port region (the busiest port in the session-12 survey sample): "
        f"{counts['berth']} berth, {counts['anchor']} anchor, {counts['ambiguous']} ambiguous. "
        "Toggle folders to see where each class falls. Berth stops cluster tightly inside "
        "San Diego Bay against known pier/base infrastructure; anchor stops sit almost "
        "entirely at a separate outer anchorage near the US-Mexico border, ~35km south of "
        "the bay entrance -- a real, physically distinct location, not classifier noise. "
        "One motion exhibit (separate folder) shows a single vessel-day arrival track "
        "linking the two: outer anchorage to bay berth."
    )

    body = "".join(stop_folders) + arrival_folder
    kml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
        "<name>San Diego port stops - M11 berth/anchor classification</name>"
        f"<description>{doc_desc}</description>"
        + STYLES + body +
        "</Document></kml>"
    )
    with open(OUT, "w") as fh:
        fh.write(kml)
    print(f"wrote {OUT} ({len(kml):,} chars)")
    print(f"stops: total={total} berth={counts['berth']} anchor={counts['anchor']} ambiguous={counts['ambiguous']}")
    print(f"arrival exhibit fixes: {n_fixes}")


if __name__ == "__main__":
    main()
