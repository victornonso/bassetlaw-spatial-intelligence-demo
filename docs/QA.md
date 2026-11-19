# Verification record — 17 November 2026

## Commands

From the project root in the dedicated virtual environment:

```powershell
.venv\Scripts\python.exe -m pip install -e '.[dev]'
.venv\Scripts\python.exe -m data_pipeline.validate --compact-flood
.venv\Scripts\python.exe -m pytest -q tests/backend data_pipeline/test_validate.py
.venv\Scripts\python.exe -m ruff check backend tests/backend
```

Observed: installation succeeded; geometry report passed; 25 tests passed, one skipped. The skipped test requires an isolated TEST_DATABASE_URL; it was not replaced by a production-data mutation. One Starlette/httpx deprecation warning remains in the test harness. Ruff passed for the backend and its tests. The compact ingestion modules are covered by explicit validation tests; they are not claimed Ruff-clean.

From frontend:

```powershell
npm run sync-data
npm run lint
npm run typecheck
npm test
npm run build
```

Observed: seven frontend tests passed. These mock the map boundary for unit-level workflow checks; actual MapLibre loading is verified in the browser separately. Vite emits a non-fatal size advisory for the lazy-loaded map chunk (about 1.06 MB uncompressed, 287 kB gzip). It is recorded, not hidden by increasing the warning limit.

## Live endpoint checks

The deployed /healthz and /readyz returned 200; readiness reported postgis connected and district data loaded. A request from Origin https://bassetlaw-demo.victorokeke.co.uk received the exact matching access-control-allow-origin value.

Retford test coordinates 53.3239,-0.9436 returned East Retford West, a loaded Flood Zone 2 intersection, nearest historical brownfield representative point at about 128 metres, nearest mapped school at about 415 metres and ten mapped schools within two kilometres. These are observed snapshot-specific results, not expected values invented for a test.

/api/layers returned one district, 25 wards, 61 schools, 1,086 flood polygons and 31 register points after the validated data release.

## Public URL and browser checks

- Custom hostname opened in a fresh Chrome tab without application authentication.
- HTTPS returned 200 with valid certificate verification; HTTP returned 308 to HTTPS.
- Map tiles, district/ward/flood/school overlays, direct point inspection, layer toggles, named location and zoom controls were exercised.
- Ward selection displayed a real profile and school-phase chart; source register displayed official links, licences and limitations.
- Desktop (1536-pixel viewport), tablet (768 × 1024) and mobile (390 × 844) layouts were inspected. No body horizontal overflow was observed at the tested narrow widths; mobile navigation scrolls horizontally by design. Temporary viewport overrides were reset.
- The production screenshot shows the full deployed desktop Planning & Growth view with a Retford Location Insight record, no loading/error state and visible attribution/disclaimer.
- Browser error log inspection returned no application errors; unrelated browser-extension warnings were present.
- Semantic navigation, labels, named-place alternatives, focus styling and textual chart values are implemented. This is a practical accessibility review, not certification. Safari was unavailable.

## QR and release assets

scripts/release_assets.py first verified the public HTTPS target. It generated 32-pixel-per-module PNG and scalable SVG assets, decoded the PNG with zxing-cpp and required the decoded text to equal https://bassetlaw-demo.victorokeke.co.uk. PNG is suitable for a PowerPoint slide; SVG remains resolution independent.

## Boundaries of verification

No GPU, medical data or RiskCal research repository changes are involved in this separate project. No fictional population, planning score or project boundary is used. Live production checks complement the skipped isolated PostGIS regression; they do not imply a comprehensive database integration test suite or uptime guarantee.

A regression test also resolves two location requests in reverse order and verifies that the latest selection remains displayed. Community requests discard responses after the selected ward changes.


## Flood geometry correction

Analytical geometry no longer uses the former 50-metre display derivative. The same source snapshot now retains 2,409 polygonal records with no analytical simplification or area filtering. Seventy-three invalid source records were repaired. An independent per-record comparison against the repaired and district-clipped source found zero changes in polygonal extent across all 2,409 records. Analytical browser cells agreed at 302 deterministic source interior/boundary points. See `data/flood_quality_report.json`.

The map uses a separate dissolved, topology-preserving, zoom-dependent display derivative, delivered as 755 vector tiles (3,033,804 bytes total; largest individual tile 89,272 bytes). It no longer fetches whole-district flood GeoJSON. Browser fallback loads only the selected unsimplified analytical cell. The maximum compressed analytical cell is 314,906 bytes. These are artifact measurements, not network timings.

Commands after the change:

```powershell
.venv/Scripts/python -m pip install -e '.[dev,pipeline]'
.venv/Scripts/python -m data_pipeline.flood
.venv/Scripts/python -m data_pipeline.validate
.venv/Scripts/python -m data_pipeline.audit_flood
.venv/Scripts/python -m pytest -q tests/backend data_pipeline/test_validate.py data_pipeline/test_flood.py
.venv/Scripts/python -m ruff check backend tests/backend data_pipeline/flood.py data_pipeline/audit_flood.py data_pipeline/test_flood.py
```

Observed: 33 backend/pipeline tests passed; one disposable PostGIS test remains skipped without TEST_DATABASE_URL. The four public-source regression points near Retford and Worksop now retain flood extents omitted by the old derivative. Frontend: 13 tests passed, including vector source selection, tile-template handling, detailed fallback classification, failed-cell behaviour and empty-cell availability. Production build passed with the existing MapLibre size advisory. Existing test-harness deprecation and vector-encoder Shapely deprecation warnings remain; neither is a runtime failure.

Local browser verification exercised district/detail views, layer toggling, zooming and a mobile viewport with the API deliberately unavailable. Real vector tiles and a detailed analytical cell loaded; no application errors, map notices or body overflow were observed. Source detail remains visibly more complex than the former derivative; genuine disconnected areas and holes are retained rather than cosmetically deleted.


Production release `7c7e35b` was verified on the custom HTTPS domain. `/api/layers` returned 2,409 flood records with `analysis_generalisation_m=0`; `/readyz` returned ready in PostGIS mode. All four public-source regression points returned their expected flood zones from PostGIS, with the exact custom-domain CORS origin. Complete evidence requests took 2.37–2.71 seconds during these checks.

Three fresh-browser runs before and after release measured flood delivery. The previous whole-layer requests took 901, 1,267 and 905 milliseconds. The new manifest plus four initial viewport vector tiles completed in 175, 127 and 112 milliseconds, transferring approximately 162 kB per run. These are observed flood-delivery timings on this connection with services available, not full-page timings, a network-independent guarantee or a cold-start benchmark. Static flood display no longer depends on Render waking up.

Production browser checks also forced the API unavailable: the detailed Retford analysis cell loaded successfully (about 268 kB compressed in that check), the map remained functional at district/detail scales, and mobile layout showed no horizontal body overflow. No application errors or map error notices were observed. The public site-preview asset and download pack were refreshed from the deployed application.


## Location Insight and community wording review

The evidence labels now name brownfield-register sites, river/sea flood zones and schools/colleges explicitly. Ward and source dates are visible; individual brownfield record dates are distinguished from catalogue/download dates. Distances are displayed once. Excluded green-space and strategic-site indicators are documented in Data & Method rather than occupying empty Location Insight sections. Calculation labels explain database/server/browser execution without implying a live provider data feed.

Communities & Services is explicitly a ward education-establishment example, with ward area, included establishment count and education-phase chart. The arbitrary ward-reference-point distance and redundant category-count indicator were removed. The source “Not applicable” phase remains visible with an explanation. Missing/failed establishment data cannot produce a false zero count in browser fallback.

Validation: 35 backend/pipeline tests passed with one isolated PostGIS test skipped (TEST_DATABASE_URL not supplied); 21 frontend tests passed. Ruff, frontend lint and production build passed. The existing Vite MapLibre size advisory and two existing Python test dependency deprecations remain. Additional regressions cover one-time distance display, source/record dates, exclusion versus failure, outside-zone wording, genuine zero subsets, and failed community data in fallback. Local real-data endpoint checks returned the updated titles and ward education profile.

Native browser visual review remains unverified. After the owner restored Chrome, Computer Use stopped because it could not determine the current browser URL confidently enough to enforce its policy. No further UI input or alternative browser automation was attempted. Automated rendering, workflow, type, build and endpoint checks are recorded separately from a visual browser review.


Production verification of wording release `254d176`: the custom-domain HTML serves the new frontend bundle, containing the revised location and community labels. The deployed API reports ready in PostGIS mode. Retford returns the explicit brownfield-register, flood-zone and school/college titles, dated ward geography, and the existing 128 m / 415 m values as separate distance fields. Worksop South returns two summary indicators, seven included establishments and the phase chart (four Primary, one Secondary, two Not applicable), with May 2024 geography and PostGIS calculation metadata. Its phase counts sum to the establishment count. Source download and individual record dates remain distinct. This endpoint verification does not substitute for the blocked browser visual review. The screenshot asset remains from the preceding flood-geometry release.
