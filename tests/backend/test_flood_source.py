"""Public-source regressions protecting real narrow extents lost by the old extract."""
import gzip
import json
from pathlib import Path

import pytest
from shapely import STRtree
from shapely.geometry import Point, shape

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / "tests/fixtures/flood-source-regressions.json").read_text())["points"]


@pytest.fixture(scope="module")
def detailed_flood():
    features = json.loads(gzip.decompress((ROOT / "data/flood_zones.geojson.gz").read_bytes()))["features"]
    return features, STRtree([shape(f["geometry"]) for f in features])


@pytest.mark.parametrize("case", CASES)
def test_narrow_source_extent_survives_release(case, detailed_flood):
    features, tree = detailed_flood
    found = tree.query(Point(case["lon"],case["lat"]), predicate="intersects")
    zones = sorted({features[index]["properties"]["flood_zone"] for index in found})
    assert zones == case["expected_zones"]
