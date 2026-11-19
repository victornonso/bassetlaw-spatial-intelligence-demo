"""Focused spatial regression tests use explicitly synthetic test-only fixtures."""
import json
from pathlib import Path

import pytest
from app import main
from app.spatial import Store
from fastapi.testclient import TestClient


def feature(identifier, geometry, **properties):
    return {"type": "Feature", "properties": {"id": identifier, "name": identifier, **properties}, "geometry": geometry}


def write_layer(directory, name, features):
    (directory / f"{name}.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": features}))


@pytest.fixture()
def client(tmp_path: Path, monkeypatch):
    # Synthetic regression geometry around Bassetlaw; not production data.
    polygon = {"type": "Polygon", "coordinates": [[[-1,53.2],[-.7,53.2],[-.7,53.5],[-1,53.5],[-1,53.2]]]}
    write_layer(tmp_path, "admin_areas", [feature("test-district", polygon)])
    write_layer(tmp_path, "wards", [feature("test-ward", polygon)])
    write_layer(tmp_path, "flood_zones", [feature("test-flood", polygon)])
    write_layer(tmp_path, "services", [feature("test-near", {"type": "Point", "coordinates": [-.9,53.3]}, service_type="School"),
                                       feature("test-far", {"type": "Point", "coordinates": [-.8,53.4]}, service_type="School")])
    (tmp_path / "dataset_registry.json").write_text(json.dumps([
        {"layer": "services", "name": "Synthetic test data", "licence": "Test only"}]))
    monkeypatch.setattr(main, "store", Store(tmp_path, database_url=""))
    return TestClient(main.app)


def test_health_and_snapshot_readiness(client):
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").json()["mode"] == "snapshot"
    assert "not configured" in client.get("/readyz").json()["detail"]


def test_intersection_and_zero_distance(client):
    result = client.get("/api/site-insight?lat=53.3&lon=-0.9").json()
    assert result["area"]["ward"] == "test-ward"
    assert result["evidence"]["flood"]["features"][0]["id"] == "test-flood"
    assert result["evidence"]["services"]["nearest"]["id"] == "test-near"
    assert result["evidence"]["services"]["distance_m"] == 0
    assert result["evidence"]["services"]["count_within_2km"] == 1


def test_nearest_distance_is_metric_and_missing_not_no_risk(client):
    result = client.get("/api/site-insight?lat=53.301&lon=-0.9").json()
    assert 100 < result["evidence"]["services"]["distance_m"] < 120
    assert result["evidence"]["planning"]["status"] == "unavailable"
    assert result["evidence"]["planning"]["summary"] == "No data loaded for this indicator"
    assert result["evidence"]["greenspace"]["distance_m"] is None


@pytest.mark.parametrize("query", ["lat=91&lon=0", "lat=53.3&lon=181", "lat=nan&lon=-.9", "lat=0&lon=0"])
def test_invalid_or_outside_coordinates(client, query):
    assert client.get("/api/site-insight?" + query).status_code == 422


def test_features_bbox_and_unknown_layer(client):
    assert client.get("/api/features/services?bbox=-.91,53.29,-.89,53.31").json()["features"][0]["properties"]["id"] == "test-near"
    assert client.get("/api/features/services?bbox=1,2,3").status_code == 422
    assert client.get("/api/features/no-such-layer").status_code == 404
    assert client.get("/api/areas/no-such-area").status_code == 404


def test_community_counts_reproduce_feature_subset(client):
    body = client.get("/api/community/test-ward").json()
    assert body["indicators"][1]["value"] == 2
    assert body["chart"]["items"] == [{"label": "School", "value": 2}]
    assert "No population" in body["limitations"][0]


def test_not_ready_without_data(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "store", Store(tmp_path, database_url=""))
    assert TestClient(main.app).get("/readyz").status_code == 503


def test_database_failure_is_readiness_failure(monkeypatch):
    class BrokenStore:
        mode = "postgis"
        def ready(self):
            raise RuntimeError("database unavailable")
    monkeypatch.setattr(main, "store", BrokenStore())
    assert TestClient(main.app).get("/readyz").status_code == 503

def test_snapshot_discovers_new_file_and_refreshes_updates(tmp_path):
    store = Store(tmp_path, database_url="")
    assert store.features("services") == []
    point = {"type": "Point", "coordinates": [-.9, 53.3]}
    write_layer(tmp_path, "services", [feature("first", point)])
    assert len(store.features("services")) == 1
    write_layer(tmp_path, "services", [feature("first", point), feature("second", point)])
    assert len(store.features("services")) == 2

def test_planning_representative_point_is_proximity_not_intersection(client):
    from app import main
    point = {"type": "Point", "coordinates": [-.91,53.3]}
    write_layer(main.store.data_dir, "planning_context", [feature("brownfield", point)])
    planning = client.get("/api/site-insight?lat=53.3&lon=-.9").json()["evidence"]["planning"]
    assert planning["nearest"]["id"] == "brownfield"
    assert planning["distance_m"] > 500
    assert planning["features"] == []
    assert "not a site boundary or allocation" in planning["summary"]

def test_missing_green_data_does_not_report_zero_services(client):
 result=client.get('/api/site-insight?lat=53.3&lon=-.9').json()
 assert result['evidence']['greenspace']['count_within_2km'] is None

def test_flood_zone_code_uses_source_field(client):
 from app import main
 polygon={'type':'Polygon','coordinates':[[[-1,53.2],[-.7,53.2],[-.7,53.5],[-1,53.5],[-1,53.2]]]}
 write_layer(main.store.data_dir,'flood_zones',[feature('zone3',polygon,flood_zone='FZ3')])
 assert 'Flood Zone 3' in client.get('/api/site-insight?lat=53.3&lon=-.9').json()['evidence']['flood']['summary']


def test_losslessly_compressed_detailed_flood_snapshot(tmp_path):
    import gzip

    from shapely.geometry import Point
    polygon = {'type':'Polygon','coordinates':[[[-.9,53.3],[-.899999,53.3],
               [-.899999,53.300001],[-.9,53.300001],[-.9,53.3]]]}
    document = {'type':'FeatureCollection','features':[feature('tiny',polygon,flood_zone='FZ2')]}
    (tmp_path / 'flood_zones.geojson.gz').write_bytes(gzip.compress(json.dumps(document).encode()))
    store = Store(tmp_path, database_url='')
    assert store.intersections('flood_zones',Point(-.8999995,53.3000005))[0]['id'] == 'tiny'
    assert store.intersections('flood_zones',Point(-.899998,53.3000005)) == []
