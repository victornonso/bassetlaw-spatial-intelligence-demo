"""Source-detail flood analysis and independent, zoom-dependent map delivery.

No simplification or minimum-area filtering is applied to analysis. Display
geometry is dissolved, simplified at a fraction of a screen pixel with topology
preserved, and tiled. It must never be used for point-in-polygon evidence.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from pyproj import Transformer
from shapely import STRtree, from_wkb, make_valid, to_wkb, union_all
from shapely import transform as shapely_transform
from shapely.geometry import GeometryCollection, MultiPolygon, box, mapping, shape

MIN_ZOOM = 8
MAX_ZOOM = 14
ANALYSIS_ZOOM = 13
EXTENT = 8192
WORLD = 20037508.342789244
PROJECT = Transformer.from_crs(4326, 3857, always_xy=True).transform
UNPROJECT = Transformer.from_crs(3857, 4326, always_xy=True).transform


def transform(project, geometry):
    return shapely_transform(geometry, project, interleaved=False)


def polygonal(geometry):
    """Retain every polygon component and hole, including tiny components."""
    if geometry.geom_type in {"Polygon", "MultiPolygon"}:
        return geometry
    if not isinstance(geometry, GeometryCollection):
        return MultiPolygon()
    parts = []
    for item in geometry.geoms:
        result = polygonal(item)
        if result.geom_type == "Polygon":
            parts.append(result)
        else:
            parts.extend(result.geoms)
    return MultiPolygon(parts)


def extract(raw: list[dict[str, Any]], boundary) -> dict[str, Any]:
    features = []
    for index, source in enumerate(raw):
        geometry = shape(source["geometry"])
        if not geometry.is_valid:
            geometry = make_valid(geometry)
        if not geometry.intersects(boundary):
            continue
        geometry = polygonal(geometry.intersection(boundary))
        if geometry.is_empty:
            continue  # Touching line/point has no polygonal flood area.
        if not geometry.is_valid:
            raise ValueError(f"Invalid flood polygon after clipping: {index}")
        zone = source["properties"]["flood_zone"]
        features.append({"type": "Feature", "geometry": mapping(geometry), "properties": {
            "id": f"{zone}-{index}", "name": "Flood Zone " + zone.replace("FZ", ""),
            "flood_zone": zone, "provider": "Environment Agency", "generalisation_m": 0,
        }})
    return {"type": "FeatureCollection", "features": features}


def tile_bounds(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    size = 2 * WORLD / 2**z
    west, north = -WORLD + x * size, WORLD - y * size
    return west, north - size, west + size, north


def tile_range(bounds, zoom: int):
    west, south = PROJECT(bounds[0], bounds[1])
    east, north = PROJECT(bounds[2], bounds[3])
    size = 2 * WORLD / 2**zoom
    return (range(math.floor((west + WORLD) / size), math.floor((east + WORLD) / size) + 1),
            range(math.floor((WORLD - north) / size), math.floor((WORLD - south) / size) + 1))


def json_bytes(value) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode("utf-8")


def build(root: Path) -> dict[str, Any]:
    import mapbox_vector_tile

    source = root / ".cache/public-data/flood.json"
    raw = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw = raw["features"]
    boundary = shape(json.loads((root / "data/admin_areas.geojson").read_text())["features"][0]["geometry"])
    collection = extract(raw, boundary)
    content = json_bytes(collection)
    revision = hashlib.sha256(content).hexdigest()[:12]
    data_dir = root / "data"
    (data_dir / "flood_zones.geojson.gz").write_bytes(gzip.compress(content, mtime=0))
    old = data_dir / "flood_zones.geojson"
    if old.exists():
        old.unlink()  # Replaced only after the complete detailed extract exists.

    geometries = [shape(f["geometry"]) for f in collection["features"]]
    tree = STRtree(geometries)
    # One combined display coverage removes internal source-feature boundaries
    # and overlapping fill. Global-per-zoom simplification cannot independently
    # move two copies of a shared boundary. Analytical records remain separate.
    union_path = root / ".cache" / f"flood-display-{revision}.wkb"
    if union_path.exists():
        display = from_wkb(union_path.read_bytes())
    else:
        print("Flood map: dissolving display coverage (analysis remains unchanged)", flush=True)
        display = union_all(geometries)
        union_path.write_bytes(to_wkb(display))
    projected_display = transform(PROJECT, display)
    map_root = data_dir / "flood-map" / revision
    analysis_root = data_dir / "flood-analysis" / revision
    cells = []
    analysis_sizes = []
    xs, ys = tile_range(boundary.bounds, ANALYSIS_ZOOM)
    for x in xs:
        for y in ys:
            # This clip is in WGS84, exactly as the analytical extract. No map
            # quantisation, coordinate rounding or simplification enters analysis.
            bounds = tile_bounds(ANALYSIS_ZOOM, x, y)
            west, south = UNPROJECT(bounds[0], bounds[1])
            east, north = UNPROJECT(bounds[2], bounds[3])
            # Sub-millimetre overlap avoids losing boundary-only intersections
            # when a point lies exactly on an analytical cell edge.
            cell = box(west - 1e-9, south - 1e-9, east + 1e-9, north + 1e-9)
            features = []
            for index in tree.query(cell, predicate="intersects"):
                geometry = polygonal(geometries[index].intersection(cell))
                if geometry.is_empty:
                    continue
                features.append({**collection["features"][index], "geometry": mapping(geometry)})
            if features:
                path = analysis_root / str(x) / f"{y}.geojson"
                path.parent.mkdir(parents=True, exist_ok=True)
                cell_content = json_bytes({"type": "FeatureCollection", "features": features})
                path.write_bytes(cell_content)
                cells.append(f"{x}/{y}")
                analysis_sizes.append(len(gzip.compress(cell_content)))
    tile_sizes = []
    for zoom in range(MIN_ZOOM, MAX_ZOOM + 1):
        # 1/8 of one 512px map tile pixel; at maxzoom 14 approximately 0.36m
        # on the ground here. This is a display tolerance, not source accuracy.
        tolerance = 2 * WORLD / 2**zoom / 4096
        zoom_display = projected_display.simplify(tolerance, preserve_topology=True)
        projected = list(zoom_display.geoms) if zoom_display.geom_type == "MultiPolygon" else [zoom_display]
        projected_tree = STRtree(projected)
        xs, ys = tile_range(boundary.bounds, zoom)
        for x in xs:
            for y in ys:
                bounds = tile_bounds(zoom, x, y)
                buffer = (bounds[2] - bounds[0]) * 16 / EXTENT
                cell = box(*bounds).buffer(buffer, join_style="mitre")
                features = []
                for index in projected_tree.query(cell, predicate="intersects"):
                    geometry = polygonal(projected[index].intersection(cell))
                    if not geometry.is_empty:
                        features.append({"geometry": geometry, "properties": {"context": "Flood Zones 2 and 3"}})
                content = mapbox_vector_tile.encode({"name": "flood_zones", "features": features},
                    default_options={"quantize_bounds": bounds, "extents": EXTENT})
                path = map_root / str(zoom) / str(x) / f"{y}.pbf"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
                tile_sizes.append(len(content))
        print(f"Flood map: built zoom {zoom}", flush=True)
    manifest = {"tilejson": "3.0.0", "name": "Environment Agency flood zones",
                "scheme": "xyz", "tiles": [f"/data/flood-map/{revision}/{{z}}/{{x}}/{{y}}.pbf"],
                "minzoom": MIN_ZOOM, "maxzoom": MAX_ZOOM, "bounds": list(boundary.bounds),
                "attribution": "© Environment Agency; Open Government Licence",
                "revision": revision, "feature_count": len(collection["features"])}
    (data_dir / "flood-map.json").write_bytes(json_bytes(manifest))
    index = {"zoom": ANALYSIS_ZOOM, "cells": cells, "revision": revision,
             "template": f"/data/flood-analysis/{revision}/{{x}}/{{y}}.geojson",
             "feature_count": len(collection["features"])}
    (data_dir / "flood-analysis.json").write_bytes(json_bytes(index))
    report = {"status": "pass", "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "analysis_sha256": hashlib.sha256(json_bytes(collection)).hexdigest(),
              "revision": revision, "source_features": len(raw), "analysis_features": len(geometries),
              "simplification_m": 0, "minimum_area_filter": None,
              "map_quantisation_extent": EXTENT, "map_maxzoom": MAX_ZOOM,
              "map_simplification": "Global dissolved display coverage; topology-preserving 1/8 screen pixel at each zoom; never used for analysis",
              "map_tiles": len(tile_sizes), "map_bytes": sum(tile_sizes),
              "max_map_tile_bytes": max(tile_sizes, default=0),
              "analysis_cells": len(cells), "max_analysis_cell_gzip_bytes": max(analysis_sizes, default=0)}
    (data_dir / "flood_quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(build(Path(__file__).resolve().parents[1]), indent=2))
