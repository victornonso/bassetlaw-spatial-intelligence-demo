# Deployment record

Verified 17 November 2026. This is an independent interview prototype, not a Council service.

## Live resources

| Component | Provider | Resource |
|---|---|---|
| Repository | GitHub | https://github.com/victornonso/bassetlaw-spatial-intelligence-demo |
| Frontend | Vercel Hobby | https://bassetlaw-spatial-intelligence-demo.vercel.app |
| Custom frontend | Vercel + Cloudflare DNS | https://bassetlaw-demo.victorokeke.co.uk |
| API | Render Free | https://bassetlaw-spatial-intelligence-demo.onrender.com |
| Database | Supabase Free | Project awoaxaoypiofvyxdliak, Europe Ireland |

The repository main branch triggers both production deployments. Vercel uses the frontend root, npm build command and dist output. VITE_API_BASE_URL can override the verified production API default; local Vite uses its proxy to localhost:8000.

## Database and API

The versioned migration enables PostGIS, creates registry/feature tables and spatial GiST indexes. The loader validates snapshots and loads them transactionally. Production readiness has been observed in postgis mode, and actual location intersection, nearest-school distance and ward-profile queries have returned data. Health and readiness are separate endpoints:

- /healthz: process liveness
- /readyz: database connectivity, PostGIS and district-data presence

Render build command:

```sh
pip install -r requirements.txt && pip install --no-deps -e . && python backend/manage.py migrate && python backend/manage.py load
```

Start command:

```sh
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

DATABASE_URL is stored only as a Render secret using the Supabase session pooler and TLS. The Data API is disabled; the browser does not receive database credentials. CORS_ORIGINS permits the two exact frontend origins listed above. Frontend headers are defined in frontend/vercel.json; API responses add security headers.

The bounded prototype currently uses the provisioning database role for migrations, ingestion and API reads. This is a documented hardening limitation: separate migration credentials and a read-only application role before operational use. No manual production table changes replace migrations.

## Costs and interview reliability

All newly created resources use free plans. No recurring paid service was purchased. Existing personal-domain renewal remains the owner's existing arrangement. Free Render services sleep and the dashboard warns that cold starts can take 50 seconds or more. Supabase Free can also pause after inactivity. Open the site before the interview and check readiness; do not depend on this as an uptime guarantee. For guaranteed availability, obtain approval for the smallest always-on Render plan actually offered by the provider. No automatic paid upgrade is configured.

A ten-second frontend timeout uses packaged public snapshots when the API is unavailable. Analysis mode is clearly labelled; fallback computes real intersections and straight-line geodesic distances over the documented extracts, whereas PostGIS uses British National Grid planar measurements. The map and source register remain useful. Public OpenStreetMap tiles are an external dependency and this is a low-volume demonstration, not a high-traffic service.

## Domain safety

Only the exact bassetlaw-demo CNAME was added in Cloudflare. The original root, www and two verification TXT records were retained. See DOMAIN_SETUP.md for Vercel's actual required target and release verification status.

## Verification

See QA.md for exact commands and observed results. A skipped isolated PostGIS regression test is explicitly distinguished from live production endpoint checks. The screenshot is captured from the public deployment, and QR generation verifies HTTPS and decodes the generated image before copying assets.
