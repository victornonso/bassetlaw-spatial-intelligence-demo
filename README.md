# Bassetlaw Spatial Intelligence Prototype

**From maps to decisions.** Independent interview prototype by Victor Okeke. Not an official Bassetlaw District Council service.

A map-led public-data application demonstrating how governed spatial evidence can support Planning and Growth, community profiles and organisational integration. It makes no assessment of Bassetlaw's current GIS capabilities and no development recommendations.

## Product

Planning and Growth combines ward context, Environment Agency flood intersections, nearest mapped schools and brownfield-register representative-point context. Every result carries sources. Missing indicators are explicitly unavailable. Communities shows calculated ward area and counts of loaded schools by educational phase, with a restrained bar chart. Strategic Change explains common identifiers and data exchange without pretending to reproduce internal systems.

The spatial workspace is about 70% map and 30% evidence panel on desktop, with stacked mobile layout. Controls use conventional checkboxes, a persistent legend, named-location alternatives and reset view. No accounts, tracking cookies, suitability scores or invented population figures are used.

## Architecture

Python ingestion and Shapely validation produce licensed WGS84 snapshots. PostgreSQL/PostGIS stores geometries and source metadata with GiST indexes; FastAPI performs intersections and metric-distance queries. React/TypeScript/Vite and MapLibre display the evidence. A clearly labelled local/browser snapshot fallback keeps the interface useful when the API is unavailable. Backend distance uses British National Grid planar metres; browser fallback uses geodesic point/centroid distances and states that distinction. Neither method is transport-network analysis.

## Visual system

Verified public CSS: https://www.bassetlaw.gov.uk/css/Bassetlaw-District-Council-Min.css

- Primary #4D7A7A, RGB 77 122 122, `.btn-teal` and `.backteal2`.
- Dark #3E6362, RGB 62 99 98, button border/control emphasis.
- Secondary #009494, RGB 0 148 148, `.backteal` and hover treatment.
- System sans-serif typography, thin borders, white/off-white backgrounds, minimal corner rounding. Flood symbology uses a separate muted blue.

The colour relationship is deliberate; the Council logo and official-service identity are not copied. See frontend/BRANDING.md.

## Local setup

Python 3.11+ and Node.js 22+ are required. From this directory:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e '.[dev]'
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd frontend
npm ci
npm run sync-data
npm run dev
```

Open http://localhost:5173. Vite proxies API requests to port 8000. Do not put database secrets in frontend variables. Without DATABASE_URL the backend explicitly reports snapshot mode. With DATABASE_URL it uses real PostGIS queries; see backend/README.md and versioned migrations.

## Refresh and validation

```powershell
.venv\Scripts\python -m data_pipeline.download --use-cache
.venv\Scripts\python -m data_pipeline.validate
.venv\Scripts\python -m pytest -q tests/backend data_pipeline/test_validate.py
cd frontend
npm test
npm run build
```

The GIAS national ZIP uses the official bulk-download workflow; supply a downloaded ZIP with --gias-zip PATH if the ignored cache is absent. This intentional manual acquisition step is documented rather than claiming an unsupported automatic download API. All transformations and loaded snapshots are reproducible. Raw national files are ignored. A refresh changes the snapshot and must be reviewed before release.

## Data and interpretation

See docs/DATA_SOURCES.md and the machine-readable data/dataset_registry.json for endpoints, licences, retrieval dates, vintage, fields, transformations and limitations. The current extracts comprise ONS historical 2024 boundaries, EA Flood Map for Planning, Bassetlaw brownfield-register points and DfE public school locations. Basemap: OpenStreetMap contributors (ODbL); respect the public tile service policy https://operations.osmfoundation.org/policies/tiles/. This small interview demo is not configured for high-volume public traffic.

Ward boundaries are historical generalisations. Brownfield points are not site boundaries, planning allocations or evidence of current permission. School proximity does not indicate catchment entitlement, capacity or quality. Flood polygons are generalised for this demonstration; always consult official planning evidence for a real site. No green-space or Census indicator is shown without a loaded dataset. No restricted OS data is used.

## Deployment and domain

Target architecture: Vercel frontend, Render API, Supabase PostgreSQL/PostGIS. See docs/DEPLOYMENT.md and docs/DOMAIN_SETUP.md for actual status and provider-issued domain values. Never infer deployment success from configuration files. No paid hosting has been purchased. Free Render cold starts are a known interview-day risk; an always-on upgrade requires owner approval.

## Interview materials

presentation_assets/end-slide-copy.txt contains proposed presentation copy. The production screenshot and QR assets are gated on a working deployed HTTPS custom domain. A local preview is not a production screenshot. See docs/DEMO_SCRIPT.md for a concise walkthrough and likely panel questions.

## Verified provider resources

GitHub: https://github.com/victornonso/bassetlaw-spatial-intelligence-demo

API: https://bassetlaw-spatial-intelligence-demo.onrender.com. Health, readiness (PostGIS mode) and a real Retford insight query verified on 17 November 2026. Supabase project reference awoaxaoypiofvyxdliak. The production frontend defaults to this verified public API URL; VITE_API_BASE_URL can override it. No database credential is committed.
