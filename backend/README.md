# Backend operation

This is an independent interview prototype using public-data snapshots. It is not a council service or planning advice.

## Local execution

From the repository root, create a Python 3.11+ virtual environment, then run:

```powershell
python -m pip install -e '.[dev]'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
python -m pytest -q
python -m ruff check backend tests/backend
```

With no `DATABASE_URL`, the API explicitly reports `snapshot` mode. Shapely evaluates actual loaded GeoJSON geometries. EPSG:4326 inputs are projected to British National Grid (EPSG:27700) for planar distances and area. Distances refer to the nearest loaded geometry, not a route, entrance, travel time, service capacity or access entitlement. Missing flood/planning/green-space data returns unavailable, never a negative risk classification. Geographic service counts reflect only the loaded service extract.

## PostGIS production execution

Create a Supabase project and obtain its backend-only PostgreSQL connection string. Enable the PostGIS extension in the Supabase dashboard's Database / Extensions view (or run the migration as the database owner where permitted). Run `migrations/001_spatial_data.sql` using that administrative connection, then load the validated snapshots with `python backend/manage.py load`. The migration CLI is `python backend/manage.py migrate`. Both commands read `DATABASE_URL` from the environment. Configure the API with a least-privilege database role that has SELECT on `dataset_registry` and `spatial_features`, and schema USAGE. Keep migration/ingestion credentials separate from the API role. Do not expose either connection string in Vite variables.

The migration creates a version record, source registry, primary keys and GiST indexes for WGS84 geometry and British National Grid transformed geometry. Point intersections use `ST_Intersects`. Nearest features use indexed KNN ordering on `ST_Transform(geom,27700)` and `ST_Distance`. Counts within two kilometres use `ST_DWithin`. Community profiles count loaded services intersecting the selected ward. No Census values or scores are fabricated.

Set `DATABASE_URL` to activate PostGIS mode. `/readyz` executes a PostGIS connectivity check and verifies district data exists; `/healthz` is process liveness only. Failed readiness returns HTTP 503. The Render blueprint is configuration only, not evidence of deployment. A free sleeping service may cause cold starts and is not recommended for an interview without checking its latency beforehand. Paid service activation requires the owner's approval.

`CORS_ORIGINS` is a comma-separated exact origin list. It must include the actual Vercel deployment origin and the custom domain; wildcard CORS is rejected at startup. Configure Render's Python version and start command from `render.yaml`. Confirm health and readiness independently after deploying. Production resources, applied migrations and verified endpoints are recorded in docs/DEPLOYMENT.md. The provisioning role is currently shared by ingestion and reads; separate roles are a documented hardening limitation.

## Tests and limits

Unit and HTTP regression tests use clearly synthetic test-only fixtures, separate from production snapshots. They test intersections, metric nearest distance, unavailable data, outside/invalid coordinates, bounding boxes, geographic counts and readiness failure. PostGIS live integration requires an actual PostgreSQL/PostGIS service; passing snapshot tests does not validate a deployed database. The API is read-only and bounded to 10,000 returned features per layer query; larger future datasets should use vector tiles or server pagination.
