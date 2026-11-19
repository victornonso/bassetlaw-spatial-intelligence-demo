"""HTTP interface for the independent public-data prototype."""
from __future__ import annotations

import logging
import math
import os
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from .spatial import LAYERS, Store, identifier

app = FastAPI(title="Bassetlaw Spatial Intelligence Prototype", version="0.1.0")
origins = [x.strip() for x in os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,https://bassetlaw-demo.victorokeke.co.uk"
).split(",") if x.strip()]
if "*" in origins:
    raise RuntimeError("Wildcard CORS is not permitted")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET"], allow_headers=["Content-Type"])
app.add_middleware(GZipMiddleware, minimum_size=1000)
store = Store()
log = logging.getLogger(__name__)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "public, max-age=60" if response.status_code == 200 else "no-store"
    return response


@app.exception_handler(Exception)
async def unavailable(request, exc):
    log.exception("Analysis request failed", exc_info=exc)
    return JSONResponse(status_code=503, content={"detail": "Live analysis is temporarily unavailable."})


@app.get("/healthz")
def health():
    return {"status": "ok", "service": "independent-interview-prototype"}


@app.get("/readyz")
def ready():
    try:
        ok, detail = store.ready()
        return JSONResponse(status_code=200 if ok else 503,
                            content={"status": "ready" if ok else "not-ready", "mode": store.mode, "detail": detail})
    except Exception:  # noqa: BLE001 - readiness must return 503 for every connection/configuration failure
        return JSONResponse(status_code=503,
                            content={"status": "not-ready", "mode": store.mode, "detail": "Data connection unavailable"})


@app.get("/api/layers")
def layers():
    registry = {r.get("layer", r.get("id")): r for r in store.registry()}
    result = []
    for key, name in LAYERS.items():
        count = store.count(key)
        result.append({"id": key, "name": name, "available": count > 0,
                       "feature_count": count, "source": registry.get(key)})
    return {"mode": store.mode, "layers": result}


@app.get("/api/areas")
def areas():
    return {"areas": [{**f["properties"], "id": identifier(f["properties"], i)}
                      for i, f in enumerate(store.features("wards"))]}


@app.get("/api/areas/{area_id}")
def area(area_id: str):
    found = next((f for i, f in enumerate(store.features("wards"))
                  if identifier(f["properties"], i) == area_id), None)
    if found is None:
        raise HTTPException(404, "Geography not found")
    return found


@app.get("/api/community/{area_id}")
def community(area_id: str):
    result = store.community(area_id)
    if result is None:
        raise HTTPException(404, "Geography not found")
    return result


@app.get("/api/site-insight")
def insight(lat: Annotated[float, Query(ge=-90, le=90)], lon: Annotated[float, Query(ge=-180, le=180)]):
    if not math.isfinite(lat) or not math.isfinite(lon):
        raise HTTPException(422, "Coordinates must be finite")
    try:
        return store.insight(lat, lon)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/features/{layer}")
def features(layer: str, bbox: str | None = None):
    if layer not in LAYERS:
        raise HTTPException(404, "Unknown layer")
    extent = None
    if bbox:
        try:
            extent = [float(v) for v in bbox.split(",")]
            if (len(extent) != 4 or not all(math.isfinite(v) for v in extent)
                    or not -180 <= extent[0] < extent[2] <= 180 or not -90 <= extent[1] < extent[3] <= 90):
                raise ValueError
        except ValueError as exc:
            raise HTTPException(422, "bbox must be west,south,east,north in WGS84") from exc
    return {"type": "FeatureCollection", "features": store.features(layer, extent)}
