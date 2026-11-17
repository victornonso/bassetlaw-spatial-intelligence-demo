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

Observed: six frontend tests passed. These mock the map boundary for unit-level workflow checks; actual MapLibre loading is verified in the browser separately. Vite emits a non-fatal size advisory for the lazy-loaded map chunk (about 1.06 MB uncompressed, 287 kB gzip). It is recorded, not hidden by increasing the warning limit.

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
