"""Data access and reproducible spatial methods. No inferred negative risk results."""
from __future__ import annotations

import gzip
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from pyproj import Transformer
from shapely import transform as shapely_transform
from shapely.geometry import Point, box, shape

ROOT = Path(__file__).resolve().parents[2]
LAYERS = {
    "admin_areas": "District boundary",
    "wards": "Wards (May 2024)",
    "services": "Schools and colleges",
    "green_spaces": "Green space",
    "flood_zones": "River and sea flood zones",
    "planning_context": "Brownfield register sites",
    "strategic_sites": "Strategic development sites",
}
PROJECT = Transformer.from_crs(4326, 27700, always_xy=True).transform


def transform(project, geometry):
    return shapely_transform(geometry, project, interleaved=False)


def identifier(properties: dict[str, Any], index: int = 0) -> str:
    return str(properties.get("id", properties.get("code", index)))


class Store:
    def __init__(self, data_dir: Path | None = None, database_url: str | None = None):
        self.data_dir = data_dir or Path(os.getenv("DATA_DIR", ROOT / "data"))
        self.database_url = database_url if database_url is not None else os.getenv("DATABASE_URL", "")
        self.mode = "postgis" if self.database_url else "snapshot"
        self._cache: dict[str, list[dict[str, Any]]] = {}
        self._mtimes: dict[str, tuple[int, int]] = {}

    def connection(self):
        import psycopg
        return psycopg.connect(self.database_url, connect_timeout=5)

    def registry(self) -> list[dict[str, Any]]:
        if self.database_url:
            with self.connection() as conn:
                return [row[0] for row in conn.execute("SELECT metadata FROM dataset_registry ORDER BY layer")]
        path = self.data_dir / "dataset_registry.json"
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, list) else data.get("datasets", [])

    def features(self, layer: str, bbox: list[float] | None = None) -> list[dict[str, Any]]:
        if layer not in LAYERS:
            raise KeyError(layer)
        if self.database_url:
            with self.connection() as conn:
                sql = "SELECT feature_id, properties, ST_AsGeoJSON(geom)::json FROM spatial_features WHERE layer = %s"
                params: list[Any] = [layer]
                if bbox:
                    sql += " AND geom && ST_MakeEnvelope(%s,%s,%s,%s,4326)"
                    params += bbox
                rows = conn.execute(sql + " ORDER BY feature_id LIMIT 10000", params).fetchall()
                return [{"type": "Feature", "id": r[0], "properties": r[1], "geometry": r[2]} for r in rows]
        path = self.data_dir / f"{layer}.geojson"
        if not path.exists():
            path = path.with_suffix(".geojson.gz")
        if not path.exists():
            return []
        stat = path.stat()
        modified = (stat.st_mtime_ns, stat.st_size)
        if layer not in self._cache or self._mtimes.get(layer) != modified:
            content = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
            self._cache[layer] = json.loads(content.decode("utf-8-sig"))["features"]
            self._mtimes[layer] = modified
        features = self._cache[layer]
        if bbox:
            envelope = box(*bbox)
            features = [f for f in features if shape(f["geometry"]).intersects(envelope)]
        return features

    def count(self, layer: str) -> int:
        if self.database_url:
            with self.connection() as conn:
                return conn.execute("SELECT count(*) FROM spatial_features WHERE layer=%s", (layer,)).fetchone()[0]
        return len(self.features(layer))

    def geometry_types(self, layer: str) -> set[str]:
        if self.database_url:
            with self.connection() as conn:
                rows = conn.execute("SELECT DISTINCT ST_GeometryType(geom) FROM spatial_features WHERE layer=%s",
                                    (layer,)).fetchall()
                return {row[0].replace("ST_", "") for row in rows}
        return {f["geometry"]["type"] for f in self.features(layer)}

    def intersections(self, layer: str, point: Point) -> list[dict[str, Any]]:
        if self.database_url:
            with self.connection() as conn:
                if layer == "flood_zones":
                    rows = conn.execute(
                        "SELECT DISTINCT f.feature_id,f.properties FROM spatial_feature_parts p "
                        "JOIN spatial_features f USING(layer,feature_id) WHERE p.layer=%s AND "
                        "ST_Intersects(p.geom,ST_SetSRID(ST_Point(%s,%s),4326)) ORDER BY f.feature_id",
                        (layer, point.x, point.y),
                    ).fetchall()
                    return [r[1] for r in rows]
                rows = conn.execute(
                    "SELECT properties FROM spatial_features WHERE layer=%s AND "
                    "ST_Intersects(geom, ST_SetSRID(ST_Point(%s,%s),4326)) ORDER BY feature_id",
                    (layer, point.x, point.y),
                ).fetchall()
                return [r[0] for r in rows]
        return [f["properties"] for f in self.features(layer) if shape(f["geometry"]).intersects(point)]

    def nearest(self, layer: str, point: Point) -> tuple[dict[str, Any] | None, float | None, int]:
        if self.database_url:
            with self.connection() as conn:
                # The EPSG:27700 functional GiST index supports this planar distance query.
                row = conn.execute(
                    "SELECT properties, ST_Distance(ST_Transform(geom,27700), "
                    "ST_Transform(ST_SetSRID(ST_Point(%s,%s),4326),27700)) AS distance "
                    "FROM spatial_features WHERE layer=%s ORDER BY ST_Transform(geom,27700) <-> "
                    "ST_Transform(ST_SetSRID(ST_Point(%s,%s),4326),27700), feature_id LIMIT 1",
                    (point.x, point.y, layer, point.x, point.y),
                ).fetchone()
                count = conn.execute(
                    "SELECT count(*) FROM spatial_features WHERE layer=%s AND "
                    "ST_DWithin(ST_Transform(geom,27700), "
                    "ST_Transform(ST_SetSRID(ST_Point(%s,%s),4326),27700),2000)",
                    (layer, point.x, point.y),
                ).fetchone()[0]
                return (row[0], float(row[1]), count) if row else (None, None, count)
        projected = transform(PROJECT, point)
        distances = [(f["properties"], projected.distance(transform(PROJECT, shape(f["geometry"]))))
                     for f in self.features(layer)]
        if not distances:
            return None, None, 0
        nearest = min(distances, key=lambda item: item[1])
        return nearest[0], nearest[1], sum(d <= 2000 for _, d in distances)

    def ready(self) -> tuple[bool, str]:
        if self.database_url:
            with self.connection() as conn:
                conn.execute("SELECT PostGIS_Version()")
                count = conn.execute("SELECT count(*) FROM spatial_features WHERE layer='admin_areas'").fetchone()[0]
                missing = conn.execute(
                    "SELECT EXISTS(SELECT 1 FROM spatial_features f WHERE f.layer='flood_zones' "
                    "AND NOT EXISTS(SELECT 1 FROM spatial_feature_parts p "
                    "WHERE p.layer=f.layer AND p.feature_id=f.feature_id))"
                ).fetchone()[0]
                if missing:
                    return False, "Detailed flood analysis index not loaded"
                return bool(count), "PostGIS connected; district data loaded" if count else "District data not loaded"
        return bool(self.features("admin_areas")), "Local public-data snapshot mode; PostGIS is not configured"

    def sources(self, layers: list[str]) -> list[dict[str, Any]]:
        return [r for r in self.registry() if r.get("layer", r.get("id")) in layers]

    def insight(self, lat: float, lon: float) -> dict[str, Any]:
        point = Point(lon, lat)
        district = self.intersections("admin_areas", point)
        if not district:
            raise ValueError("Select a location inside the loaded Bassetlaw district boundary.")
        ward = self.intersections("wards", point)
        evidence: dict[str, Any] = {}
        for key, layer, title in [("flood", "flood_zones", "River and sea flood zones"),
                                  ("planning", "planning_context", "Nearby brownfield register site"),
                                  ("growth", "strategic_sites", "Strategic development sites")]:
            loaded = self.count(layer) > 0
            if loaded and key in {"planning", "growth"} and self.geometry_types(layer) <= {"Point", "MultiPoint"}:
                nearest, distance, _ = self.nearest(layer, point)
                rounded = round(distance)
                label = "site in the loaded brownfield register" if key == "planning" else "strategic development location"
                evidence[key] = {"title": title, "status": "available", "nearest": nearest,
                                 "distance_m": rounded, "features": [],
                                 "distance_basis": "Distance to the register's mapped point, not a site boundary or allocation."
                                 if key == "planning" else "Distance to the published strategic development point.",
                                 "summary": f"Nearest {label}: {nearest.get('name', 'Unnamed')}."}
                continue
            found = self.intersections(layer, point) if loaded else []
            summary = "Dataset not included in this prototype."
            if loaded:
                summary = (f"This location intersects {len(found)} mapped feature(s). Review the source record."
                           if found else "No intersection with the loaded extract. This is not confirmation of no constraint or risk.")
            if key == "flood" and found:
                zones = sorted({str(f.get("flood_zone",f.get("zone"))).replace("FZ", "") for f in found if f.get("flood_zone", f.get("zone"))})
                if zones:
                    label = "Zone " if len(zones) == 1 else "Zones "
                    summary = "The selected point falls within Environment Agency Flood " + label + " and ".join(zones) + " in this dataset."
            if key == "flood" and loaded and not found:
                summary = ("The selected point is outside the Flood Zone 2 and 3 polygons in this dataset. "
                           "This does not establish that there is no flood risk.")
            evidence[key] = {"title": title, "status": "available" if loaded else "unavailable",
                             "summary": summary, "features": found,
                             **({"unavailable_reason": "not_included"} if not loaded else {})}
        for key, layer, title in [("greenspace", "green_spaces", "Green space"),
                                  ("services", "services", "Nearby schools and colleges")]:
            nearest, distance, count = self.nearest(layer, point)
            rounded = round(distance) if distance is not None else None
            label = "school or college in the loaded dataset" if key == "services" else "green space in the loaded dataset"
            evidence[key] = {"title": title, "status": "available" if nearest else "unavailable",
                             "nearest": nearest, "distance_m": rounded,
                             "count_within_2km": count if nearest and key == "services" else None,
                             "summary": (f"Nearest {label}: {nearest.get('name', 'Unnamed')}."
                                         if nearest else "Dataset not included in this prototype."),
                             **({"unavailable_reason": "not_included"} if not nearest else {})}
        return {"location": {"lat": lat, "lon": lon},
                "area": {"district": district[0].get("name", "Bassetlaw"),
                         "ward": ward[0].get("name") if ward else None,
                         "ward_date": ward[0].get("geography_date") if ward else None},
                "evidence": evidence,
                "sources": self.sources(list(LAYERS)),
                "method": {"mode": self.mode, "distance": "British National Grid Euclidean distance (EPSG:27700)",
                           "limitations": "Straight-line proximity is not travel time, a safe route, service capacity or planning advice."}}

    def community(self, area_id: str) -> dict[str, Any] | None:
        area = next((f for i, f in enumerate(self.features("wards"))
                     if identifier(f["properties"], i) == area_id), None)
        if area is None:
            return None
        polygon = shape(area["geometry"])
        services = [f for f in self.features("services") if polygon.intersects(shape(f["geometry"]))]
        loaded = self.count("services") > 0
        categories = Counter(f["properties"].get("phase") or f["properties"].get("category") or "Not recorded"
                             for f in services)
        indicators = [{"label": "Ward area", "value": round(transform(PROJECT, polygon).area / 1e6, 2),
                       "unit": "km²", "description": "Calculated from the included ward boundary."},
                      {"label": "Schools and colleges in this ward", "value": len(services) if loaded else "Not included",
                       "unit": "establishments" if loaded else "",
                       "description": "Establishments recorded as open in the downloaded dataset, located within this ward boundary."}]
        return {"area": area["properties"], "indicators": indicators,
                "chart": {"title": "Schools and colleges by education phase",
                          "items": [{"label": k, "value": v} for k, v in sorted(categories.items())]},
                "sources": self.sources(["wards", "services"]),
                "service_status": "available" if loaded else "not_included", "method": {"mode": self.mode},
                "limitations": ["Population, deprivation and housing-need data are not included in this profile.",
                                "This dataset includes establishments within Bassetlaw; facilities outside the district are not included."]}
