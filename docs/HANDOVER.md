# Handover: Bassetlaw Spatial Intelligence Prototype

Independent interview prototype by Victor Okeke. Not an official Bassetlaw District Council service.

## Live site and repository

- Live: https://bassetlaw-demo.victorokeke.co.uk
- Repository: https://github.com/victornonso/bassetlaw-spatial-intelligence-demo
- Backup frontend hostname: https://bassetlaw-spatial-intelligence-demo.vercel.app
- API: https://bassetlaw-spatial-intelligence-demo.onrender.com

The custom domain is active. Its managed certificate, HTTPS response and HTTP-to-HTTPS redirect were verified. No DNS action remains. Only the bassetlaw-demo CNAME was created; existing root and www records were retained.

## Architecture

Python ingestion downloads authoritative public sources and validates identifiers and geometry. PostgreSQL with the PostGIS spatial extension stores the snapshots and provenance with spatial indexes. FastAPI performs point-in-polygon, nearest-feature and distance queries. React, TypeScript and MapLibre provide the map and evidence record. Browser analysis over the same packaged public snapshots is a labelled fallback when the Application Programming Interface (API) is unavailable.

## Interface system

- Observed Bassetlaw public-site colours: #4D7A7A (RGB 77,122,122), #3E6362 (62,99,98) and #009494 (0,148,148). See frontend/BRANDING.md for official CSS selectors.
- Arial/Helvetica system sans-serif; restrained typography, thin rules and conventional controls.
- Approximately 71% map and 29% context panel on desktop. Stacked map and evidence on mobile; horizontal navigation remains scrollable.
- The supplied Council logo appears with clear independent-prototype labelling. No generic dashboard tiles, gradients, glass effects, fake key performance indicators or black-box suitability score.
- Visible independent-project disclaimer, named-location alternative to map clicking, keyboard focus states and source attribution.

## Features built

- Planning & Growth: pan/zoom, reset, layer toggles, direct point and ward inspection, named-place selection and a structured Location Insight record.
- Real ward intersections, flood intersections, nearest historical brownfield-register point, nearest mapped school and count within two kilometres.
- Communities & Services: select a ward, calculate its area, count mapped schools, show school-phase distribution and nearest service from an interior ward reference point.
- Strategic Change: a conceptual integration flow, with Unique Property Reference Number (UPRN) and Unique Street Reference Number (USRN) explanations. It makes no assertion about Bassetlaw's internal systems.
- Data & Method: provider, licence, retrieval date, attribution, method and limitations.
- Reproducible ingestion, versioned migrations, source hashes, validation report, error handling and public-snapshot fallback.

## Data sources

| Source | Licence | Official URL |
|---|---|---|
| Office for National Statistics December 2024 districts | Open Government Licence v3.0 | https://www.arcgis.com/home/item.html?id=6a05f93297cf4a438d08e972099f54b9 |
| Office for National Statistics May 2024 wards | Open Government Licence v3.0 | https://www.arcgis.com/home/item.html?id=b58c65bdad994ed3a33741eea7bb09ab |
| Environment Agency Flood Map for Planning | Open Government Licence | https://www.data.gov.uk/dataset/104434b0-5263-4c90-9b1e-e43b1d57c750/flood-map-for-planning-flood-zones1 |
| Bassetlaw Brownfield Land Register | Open Government Licence v3.0 | https://data.bassetlaw.gov.uk/brownfield-register/ |
| Department for Education public school download | Open Government Licence v3.0 | https://get-information-schools.service.gov.uk/Downloads |
| OpenStreetMap basemap | Open Database Licence | https://www.openstreetmap.org/copyright |

The loaded extract contains one district, 25 historical wards, 1,086 generalised flood polygons, 31 brownfield representative points and 61 open educational establishments. These are extract counts, not measures of Council capability. Complete licence wording, provenance and transformations are in DATA_SOURCES.md and data/dataset_registry.json. Every Bassetlaw-specific fact used is recorded with its official source in BASSETLAW_FACTS.md.

## Hosting and costs

Frontend: Vercel Hobby. Backend: Render Free. Database: Supabase Free in Europe Ireland. Cloudflare provides the subdomain DNS. No paid recurring service was purchased. Existing domain renewal is separate.

Render Free can sleep and the provider warns of cold starts of 50 seconds or more. Supabase Free can pause after inactivity. The browser fallback helps preserve an interview demonstration, but it is not a hosting uptime guarantee. For an always-on API, the smallest paid provider tier needs the owner's approval. Open the site and check readiness before the interview; never describe warm-up as guaranteed reliability.

## Verification

Backend and pipeline: 25 tests passed, one isolated PostGIS test skipped because no TEST_DATABASE_URL was provided. Production PostGIS readiness and actual spatial results were separately verified. Frontend: seven tests passed; lint, type checking and production build passed. See QA.md for exact commands and limitations. QR image decoding returned the intended custom-domain URL. The screenshot was captured from the deployed custom domain with a real Retford evidence result.

## Known limitations

- Historical 2024 boundaries are not labelled current electoral boundaries.
- Flood polygons are simplified at 50 metres; small features can disappear and boundaries shift. This is not a real planning or property-level flood assessment.
- Brownfield locations are historical representative points, not site boundaries, allocations or current permission evidence.
- School locations are one bounded service example. Distances are straight-line, not journeys, catchment entitlement, capacity or demand.
- No green-space dataset, Census population/deprivation data, strategic-project boundary or planning-allocation polygons were loaded. Missing indicators are explicit.
- Spherical Tokamak for Energy Production (STEP) / West Burton context was investigated, but no project geometry or economic claims are presented.
- Browser fallback uses geodesic distance; PostGIS uses British National Grid planar metres. Modes are visible and small differences are possible.
- The bounded API uses the provisioning database role. Separate read-only application and migration roles before operational use. Credentials remain backend-only.
- Public OpenStreetMap tiles are intended here for a small interview audience. A larger service needs an appropriate tile arrangement.
- The MapLibre bundle is lazy-loaded; its approximately 287 kB compressed chunk triggers Vite's size advisory. No runtime build error was observed.
- Safari was not available for a real-engine check. Responsive Chromium checks do not establish Safari conformance or formal Web Content Accessibility Guidelines certification.

## Interview demonstration: approximately 75 seconds

1. Open Planning & Growth. Select Retford town centre and enable Planning context. Point to the Location Insight panel: ward, flood evidence and service proximity are combined.
2. Say: “This is a small independent prototype using public data. It does not represent Bassetlaw's internal systems. Selecting a location brings different evidence together, so the question becomes what we need to consider here.”
3. Say: “The map is the interface. The useful capability is the validated data and repeatable analysis behind it. These results are traceable, and a missing dataset stays missing.”
4. Open Communities & Services, choose Worksop South and show the school counts and phase chart. Say: “The same data foundation can answer another service question. These counts describe the loaded schools; they do not measure demand or capacity.”
5. Open Data & Method. Say: “The sources, licences and limitations are visible. With agreed ownership and common location identifiers, this approach could support more council services. I would start by understanding the systems already in place.”

## Presentation introduction

“I built a small public-data prototype to show how a map can become a reusable, traceable answer to a council question.”

## Five likely panel questions

**What does this prove beyond putting layers on a map?**

Selecting a point runs spatial queries and returns an evidence record across several sources. The same data also supports ward summaries. That reuse, with traceable methods and clear limits, is the capability I wanted to demonstrate.

**Can a planner rely on the flood or brownfield result?**

It is demonstration evidence, not a planning determination. The flood geometry is generalised and the brownfield record is a point, so I would direct a real assessment to the authoritative current source and relevant professional review. I have made those limits visible.

**How would you integrate this with council systems?**

I would first understand the existing architecture, licensing and data ownership. Then I would agree common identifiers, validation rules and controlled interfaces with service teams. The prototype shows the pattern without assuming how Bassetlaw works today.

**What happens if the backend is unavailable?**

The interface can analyse packaged public snapshots and labels that mode. Its distance calculation differs slightly from the database method. For an operational service I would also address hosting availability, monitoring and database roles; the free interview hosting is not an operational service commitment.

**Why did you leave some indicators out?**

Because an unsupported value is less useful than a clearly stated gap. I chose a bounded question with evidence I could validate and licence. I would add further sources only when they answer an agreed service question and their provenance and interpretation are sound.
