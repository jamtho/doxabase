"""Render vessel-story material from the AIS study into a KML file.

The ultra-cheap map path (expert round 4): points, tracks, and labels
that Google Earth (or any KML consumer) renders directly. v1 scope:
broadcast fix-clouds for chosen vessel-day windows (the squiggles the
experts read) plus labelled story placemarks.

Usage: venv/bin/python story_kml.py OUT.kml
S3 credentials come from the environment; never copy them anywhere.
"""
import html
import os
import sys

import duckdb

OUT = sys.argv[1] if len(sys.argv) > 1 else "demo.kml"

# (name, mmsi, date, description, style) fix-cloud windows
WINDOWS = [
    ("PENNSYLVANIA at anchor (2024-05-04 00:00-04:32)", 338617000,
     "2024-05-04", "M11 showcase: swing ring around ground tackle - "
     "radius_mean 123 m, hollow_frac 0.34, heading sweeping >110° at "
     "SOG 0.0. Broadcast fixes, first 4.6 h of the day.", "anchor"),
    ("PENNSYLVANIA at berth (2024-05-05)", 338617000,
     "2024-05-05", "M11 showcase: GPS-noise point at a Tampa berth - "
     "radius_mean 3.4 m, hollow_frac 0.94, heading pinned "
     "(R=0.999997).", "berth"),
]

# (name, mmsi, description) story vessels: index top-2 dwell poles drawn
SHUTTLES = [
    ("SONNY COOK - Mississippi shuttle", 366989480,
     "M9 exemplar: Baton Rouge <-> LaPlace/Norco weekly for two years; "
     "max gap 12 days. The clean no-stoppage baseline."),
    ("ALGOMA EQUINOX - Lakes grain shuttle", 316009090,
     "M9 exemplar: Hamilton <-> Thunder Bay; ~99-day winter gap matches "
     "the Soo Locks closure; a second 115-day gap is vessel-specific."),
]

STYLES = """
<Style id="anchor"><IconStyle><color>ff0055ff</color><scale>0.5</scale>
<Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
</IconStyle><LabelStyle><scale>0</scale></LabelStyle></Style>
<Style id="berth"><IconStyle><color>ff00cc00</color><scale>0.5</scale>
<Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
</IconStyle><LabelStyle><scale>0</scale></LabelStyle></Style>
<Style id="pole"><IconStyle><color>ffff8800</color><scale>1.1</scale>
<Icon><href>http://maps.google.com/mapfiles/kml/paddle/O.png</href></Icon>
</IconStyle></Style>
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


def fix_cloud(con, name, mmsi, date, desc, style):
    year = date[:4]
    rows = con.execute(
        f"""
        SELECT longitude, latitude FROM
        read_parquet('s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet')
        WHERE mmsi = ? AND latitude IS NOT NULL
        ORDER BY base_date_time
        """,
        [mmsi],
    ).fetchall()
    pts = "".join(
        f'<Placemark><styleUrl>#{style}</styleUrl>'
        f"<Point><coordinates>{lon:.6f},{lat:.6f},0</coordinates></Point></Placemark>"
        for lon, lat in rows
    )
    return (
        f"<Folder><name>{html.escape(name)}</name>"
        f"<description>{html.escape(desc)} ({len(rows)} fixes)</description>{pts}</Folder>"
    )


def dwell_poles(con, name, mmsi, desc):
    rows = con.execute(
        """
        SELECT round(centroid_lat, 1) AS plat, round(centroid_lon, 1) AS plon,
               avg(centroid_lat) AS lat, avg(centroid_lon) AS lon, count(*) AS days
        FROM read_parquet('s3://ais-noaa/index/*/*.parquet')
        WHERE mmsi = ? AND sog_mean < 1
        GROUP BY 1, 2 ORDER BY days DESC LIMIT 2
        """,
        [mmsi],
    ).fetchall()
    marks = "".join(
        f"<Placemark><name>{html.escape(name)} pole {i+1} ({int(days)} dwell-days)</name>"
        f"<description>{html.escape(desc)}</description><styleUrl>#pole</styleUrl>"
        f"<Point><coordinates>{lon:.5f},{lat:.5f},0</coordinates></Point></Placemark>"
        for i, (_, _, lat, lon, days) in enumerate(rows)
    )
    return f"<Folder><name>{html.escape(name)}</name>{marks}</Folder>"


def main():
    con = connect()
    parts = [fix_cloud(con, *w) for w in WINDOWS]
    parts += [dwell_poles(con, *s) for s in SHUTTLES]
    body = "".join(parts)
    kml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
        "<name>AIS study - story map demo</name>" + STYLES + body +
        "</Document></kml>"
    )
    with open(OUT, "w") as fh:
        fh.write(kml)
    print(f"wrote {OUT} ({len(kml):,} chars)")


if __name__ == "__main__":
    main()
