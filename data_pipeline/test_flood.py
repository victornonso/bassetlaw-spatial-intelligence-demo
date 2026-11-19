"""Synthetic geometry regressions; no fabricated production flood evidence."""
import gzip
import json

import mapbox_vector_tile
from shapely.geometry import MultiPolygon, Point, Polygon, box, mapping, shape

from data_pipeline import flood


def test_components_holes_and_narrow_corridor_preserved():
    main = Polygon([(0,0),(1,0),(1,.00001),(2,.00001),(2,0),(3,0),(3,1),(0,1)],
                   holes=[[(.2,.2),(.4,.2),(.4,.4),(.2,.4)]])
    tiny = box(4,0,4.000001,.000001)
    source = MultiPolygon([main,tiny])
    result = flood.extract([{"geometry": mapping(source), "properties": {"flood_zone": "FZ3"}}],
                           box(-1,-1,5,2))
    restored = shape(json.loads(json.dumps(result))["features"][0]["geometry"])
    assert restored.equals(source)
    assert restored.intersects(tiny.representative_point())
    assert not restored.intersects(Point(.3,.3))
    assert len(restored.geoms) == 2
    assert sum(len(p.interiors) for p in restored.geoms) == 1


def test_build_separates_exact_analysis_from_tiled_display(tmp_path, monkeypatch):
    monkeypatch.setattr(flood, "MIN_ZOOM", 14)
    monkeypatch.setattr(flood, "MAX_ZOOM", 14)
    (tmp_path / "data").mkdir()
    (tmp_path / ".cache/public-data").mkdir(parents=True)
    boundary = box(-1.001,53.299,-.999,53.301)
    geometry = box(-1,53.3,-.999999,53.300001)
    (tmp_path / "data/admin_areas.geojson").write_text(json.dumps({"features":[{"geometry":mapping(boundary)}]}))
    (tmp_path / ".cache/public-data/flood.json").write_text(json.dumps([
        {"geometry":mapping(geometry),"properties":{"flood_zone":"FZ2"}}]))
    report = flood.build(tmp_path)
    analytical = json.loads(gzip.decompress((tmp_path / "data/flood_zones.geojson.gz").read_bytes()))
    assert shape(analytical["features"][0]["geometry"]).equals(geometry)
    assert report["simplification_m"] == 0
    assert report["minimum_area_filter"] is None
    index = json.loads((tmp_path / "data/flood-analysis.json").read_text())
    assert index["feature_count"] == 1 and index["cells"]
    point = geometry.representative_point()
    cells = list((tmp_path / "data/flood-analysis").rglob("*.geojson"))
    assert any(shape(f["geometry"]).intersects(point) for cell in cells
               for f in json.loads(cell.read_text())["features"])
    tiles = list((tmp_path / "data/flood-map").rglob("*.pbf"))
    assert tiles
    assert all("flood_zones" in mapbox_vector_tile.decode(tile.read_bytes()) for tile in tiles)


def test_invalid_source_repaired_and_line_only_clip_omitted():
    bow = Polygon([(0,0),(1,1),(1,0),(0,1),(0,0)])
    result = flood.extract([{"geometry":mapping(bow),"properties":{"flood_zone":"FZ2"}},
                            {"geometry":mapping(box(2,0,3,1)),"properties":{"flood_zone":"FZ3"}}],
                           box(-1,-1,2,2))
    assert len(result["features"]) == 1
    assert shape(result["features"][0]["geometry"]).is_valid
