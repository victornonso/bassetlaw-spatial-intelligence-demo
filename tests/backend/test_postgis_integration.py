"""Optional real PostGIS contract test. Requires a disposable TEST_DATABASE_URL database."""
import os
import uuid
from pathlib import Path

import psycopg
import pytest
from app.spatial import Store
from psycopg import sql
from psycopg.types.json import Jsonb
from shapely.geometry import Point


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="No disposable PostGIS database configured")
def test_real_postgis_intersection_and_distance():
    database_url = os.environ["TEST_DATABASE_URL"]
    schema = "spatial_test_" + uuid.uuid4().hex
    with psycopg.connect(database_url, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    try:
        with psycopg.connect(database_url, options=f"-c search_path={schema},public") as conn:
            conn.execute((Path(__file__).parents[2] / "migrations/001_spatial_data.sql").read_text(encoding="utf-8-sig"))
            conn.execute((Path(__file__).parents[2] / "migrations/002_flood_query_parts.sql").read_text(encoding="utf-8-sig"))
            conn.execute("INSERT INTO dataset_registry VALUES ('services', %s), ('wards', %s)",
                         (Jsonb({"layer": "services"}), Jsonb({"layer": "wards"})))
            conn.execute("INSERT INTO spatial_features VALUES ('services','near',%s,ST_SetSRID(ST_Point(-.9,53.3),4326)),"
                         "('wards','ward',%s,ST_MakeEnvelope(-1,53.2,-.7,53.5,4326))",
                         (Jsonb({"id": "near"}), Jsonb({"id": "ward"})))
        class SchemaStore(Store):
            def connection(self):
                return psycopg.connect(database_url, options=f"-c search_path={schema},public")
        store = SchemaStore(database_url=database_url)
        assert store.intersections("wards", Point(-.9, 53.3))[0]["id"] == "ward"
        nearest, distance, count = store.nearest("services", Point(-.9, 53.301))
        assert nearest["id"] == "near" and 100 < distance < 120 and count == 1
        with store.connection() as conn:
            conn.execute("INSERT INTO dataset_registry(layer,metadata) VALUES('flood_zones',%s)",
                         (Jsonb({"layer": "flood_zones"}),))
            conn.execute("INSERT INTO spatial_features(layer,feature_id,properties,geom) "
                         "VALUES('flood_zones','tiny',%s,ST_MakeEnvelope(-.9,53.3,-.899999,53.300001,4326))",
                         (Jsonb({"id": "tiny", "flood_zone": "FZ2"}),))
            conn.execute("INSERT INTO spatial_feature_parts(layer,feature_id,geom) "
                         "SELECT layer,feature_id,ST_Subdivide(geom,256) FROM spatial_features "
                         "WHERE layer='flood_zones'")
        assert store.intersections("flood_zones",Point(-.8999995,53.3000005))[0]["id"] == "tiny"
        assert store.intersections("flood_zones",Point(-.899998,53.3000005)) == []
    finally:
        with psycopg.connect(database_url, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
