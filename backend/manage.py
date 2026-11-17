"""Explicit migration and validated snapshot loading. Run from repository root."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import psycopg
from app.spatial import LAYERS
from psycopg.types.json import Jsonb
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]


def migrate(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        for migration in sorted((ROOT / "migrations").glob("*.sql")):
            connection.execute(migration.read_text(encoding="utf-8-sig"))
            print(f"Applied idempotent migration: {migration.name}")


def load(database_url: str, data_dir: Path) -> None:
    registry = json.loads((data_dir / "dataset_registry.json").read_text(encoding="utf-8-sig"))
    if not isinstance(registry, list):
        registry = registry["datasets"]
    prepared = []
    for record in registry:
        layer = record.get("layer", record.get("id"))
        if layer not in LAYERS:
            continue
        source = data_dir / f"{layer}.geojson"
        if not source.exists():
            continue
        document = json.loads(source.read_text(encoding="utf-8-sig"))
        if document.get("type") != "FeatureCollection":
            raise ValueError(f"{layer}: expected FeatureCollection")
        identifiers = set()
        rows = []
        for feature in document["features"]:
            properties = feature["properties"]
            feature_id = properties.get("id")
            if feature_id is None or str(feature_id) in identifiers:
                raise ValueError(f"{layer}: missing or duplicate feature identifier")
            identifiers.add(str(feature_id))
            geometry = shape(feature["geometry"])
            if geometry.is_empty or not geometry.is_valid:
                raise ValueError(f"{layer}: invalid or empty geometry {feature_id}")
            west, south, east, north = geometry.bounds
            if not (-180 <= west <= east <= 180 and -90 <= south <= north <= 90):
                raise ValueError(f"{layer}: expected WGS84 coordinate bounds")
            rows.append((layer, str(feature_id), Jsonb(properties), json.dumps(feature["geometry"])))
        prepared.append((layer, record, rows))
    if not prepared:
        raise ValueError("No registered datasets ready to load")
    # All datasets validate before any write. One transaction prevents partial refreshes.
    with psycopg.connect(database_url) as connection:
        for layer, record, rows in prepared:
            connection.execute("INSERT INTO dataset_registry(layer,metadata) VALUES(%s,%s) "
                               "ON CONFLICT(layer) DO UPDATE SET metadata=excluded.metadata,loaded_at=now()",
                               (layer, Jsonb(record)))
            connection.execute("DELETE FROM spatial_features WHERE layer=%s", (layer,))
            with connection.cursor() as cursor:
                cursor.executemany(
                    "INSERT INTO spatial_features(layer,feature_id,properties,geom) "
                    "VALUES(%s,%s,%s,ST_SetSRID(ST_GeomFromGeoJSON(%s),4326))", rows)
            print(f"Loaded {layer}: {len(rows)} validated features")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["migrate", "load"])
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    arguments = parser.parse_args()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        parser.error("Set DATABASE_URL in the environment; never pass credentials as command arguments")
    if arguments.command == "migrate":
        migrate(database_url)
    else:
        load(database_url, arguments.data_dir)


if __name__ == "__main__":
    main()
