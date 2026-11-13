"""Convert the Survey of India state boundaries (Datameet Admin2 shapefile)
into light SVG paths for the website's maps.

Run once (or when the boundary data changes):
    python3 tools/make_india_paths.py /path/to/Admin2
Output: assets/data/india_states.json  {viewBox, states: {name: "M..Z"}}

Projection: simple equirectangular with x scaled by cos(22 N), which keeps
India's shape right at web size. Simplification tolerance is 0.02 degree
(about 2 km, well under one pixel on screen), so the official outline is kept.
"""
import json, math, sys
import shapefile
from shapely.geometry import shape

src = sys.argv[1] if len(sys.argv) > 1 else "Admin2"
K = 20.0                      # pixels per degree of latitude
LON0, LAT0 = 68.0, 37.2
CX = math.cos(math.radians(22))
TOL = 0.02
ISLANDS = {"Lakshadweep", "Andaman & Nicobar"}

def xy(lon, lat):
    return (lon - LON0) * CX * K, (LAT0 - lat) * K

def ring_path(coords):
    pts = [xy(*c) for c in coords]
    out = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"
    return out

r = shapefile.Reader(src)
states, maxx, maxy = {}, 0, 0
for sr in r.iterShapeRecords():
    g = shape(sr.shape.__geo_interface__).simplify(TOL, preserve_topology=True)
    polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
    parts = []
    for p in polys:
        if p.area < 0.0004 and sr.record["ST_NM"] not in ISLANDS:  # drop coastal specks (island territories keep every island)
            continue
        parts.append(ring_path(p.exterior.coords))
        for hole in p.interiors:
            parts.append(ring_path(hole.coords))
        bx = xy(p.bounds[2], p.bounds[1])
        maxx, maxy = max(maxx, bx[0]), max(maxy, bx[1])
    states[sr.record["ST_NM"]] = "".join(parts)

json.dump({"viewBox": f"0 0 {math.ceil(maxx)+4} {math.ceil(maxy)+4}",
           "source": "Survey of India boundary via Datameet (github.com/datameet/maps)",
           "states": states},
          open("assets/data/india_states.json", "w"), ensure_ascii=False)
print("states:", len(states), "viewBox", math.ceil(maxx), math.ceil(maxy))
