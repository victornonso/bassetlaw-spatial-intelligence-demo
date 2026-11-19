"""Independently compare released analysis to the repaired/clipped public source.

This audit uses the source geometries, not the display derivative. Its coverage
checks are per source record, avoiding an expensive district-wide dissolve.
"""
import gzip
import json
import math
from pathlib import Path

from shapely import STRtree, make_valid
from shapely.geometry import shape


def audit(root: Path):
    directory = root / "data"
    raw = json.loads((root / ".cache/public-data/flood.json").read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw = raw["features"]
    boundary = shape(json.loads((directory / "admin_areas.geojson").read_text())["features"][0]["geometry"])
    released = json.loads(gzip.decompress((directory / "flood_zones.geojson.gz").read_bytes()))["features"]
    by_id = {f["properties"]["id"]: shape(f["geometry"]) for f in released}
    checked = repaired = 0
    for index, source in enumerate(raw):
        original = shape(source["geometry"])
        if not original.is_valid:
            original = make_valid(original)
            repaired += 1
        if not original.intersects(boundary):
            continue
        expected = original.intersection(boundary)
        if expected.area == 0:
            continue
        key = f"{source['properties']['flood_zone']}-{index}"
        actual = by_id[key]
        # A GeometryCollection may also contain lines/points on the clip edge;
        # symmetric-difference area checks all polygonal extent independently.
        if expected.symmetric_difference(actual).area != 0:
            raise ValueError(f"Flood analytical extent changed: {key}")
        checked += 1
    if checked != len(released):
        raise ValueError("Unexpected or missing analytical source records")

    geometries = list(by_id.values())
    tree = STRtree(geometries)
    index = json.loads((directory / "flood-analysis.json").read_text())
    cache = {}
    points = []
    # Deterministic broad sample of real source interior and boundary points.
    for geometry in geometries[::max(1, len(geometries)//150)]:
        points.extend([geometry.representative_point(), geometry.boundary.representative_point()])
    for point in points:
        n = 2**index["zoom"]
        x = math.floor((point.x+180)/360*n)
        y = math.floor((1-math.asinh(math.tan(math.radians(point.y)))/math.pi)/2*n)
        key = f"{x}/{y}"
        if key not in index["cells"]:
            raise ValueError(f"Analytical cell missing at source point {point.wkt}")
        if key not in cache:
            path = root / "frontend/public" / index["template"].lstrip("/").replace("{x}",str(x)).replace("{y}",str(y))
            cache[key] = [shape(f["geometry"]) for f in json.loads(path.read_text())["features"]]
        expected = len(tree.query(point, predicate="intersects")) > 0
        actual = any(geometry.intersects(point) for geometry in cache[key])
        if expected != actual:
            raise ValueError(f"Analytical cell disagrees at {point.wkt}")
    result = {"source_records_compared": checked, "invalid_source_records_repaired": repaired,
              "changed_polygonal_extent_records": 0, "analytical_cell_points_checked": len(points),
              "analytical_cell_disagreements": 0}
    path = directory / "flood_quality_report.json"
    report = json.loads(path.read_text())
    report["source_fidelity_audit"] = result
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(audit(Path(__file__).resolve().parents[1]), indent=2))
