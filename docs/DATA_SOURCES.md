# Data sources and methods

This independent interview prototype uses public snapshots. It does not reproduce Bassetlaw's internal systems or recommend whether a site should be developed. The machine-readable registry at `data/dataset_registry.json` is the definitive per-extract record, including retrieval timestamp, fields, hashes and exact feature counts.

## Loaded sources

| Layer | Provider and official catalogue | Licence | Source CRS / delivered CRS | Vintage and coverage |
|---|---|---|---|---|
| `admin_areas` | [ONS December 2024 local authority districts, generalised clipped](https://www.arcgis.com/home/item.html?id=6a05f93297cf4a438d08e972099f54b9) | Open Government Licence v3.0 | EPSG:27700 / EPSG:4326 | Bassetlaw E07000171; December 2024 historical snapshot |
| `wards` | [ONS May 2024 wards, generalised super-clipped](https://www.arcgis.com/home/item.html?id=b58c65bdad994ed3a33741eea7bb09ab) | Open Government Licence v3.0 | EPSG:27700 / EPSG:4326 | May 2024 geography selected around Bassetlaw; historical boundaries explicitly retained |
| `flood_zones` | [Environment Agency Flood Map for Planning: Flood Zones](https://www.data.gov.uk/dataset/104434b0-5263-4c90-9b1e-e43b1d57c750/flood-map-for-planning-flood-zones1) | Open Government Licence | EPSG:27700 / EPSG:4326 | Official catalogue revised 21 October 2026; Bassetlaw extract |
| `planning_context` | [Bassetlaw Brownfield Land Register](https://data.bassetlaw.gov.uk/brownfield-register/) | Open Government Licence v3.0 | EPSG:27700 / EPSG:4326 | Catalogue updated 28 September 2026; individual CSV records retain their own dates |
| `services` | [DfE Get Information about Schools public bulk downloads](https://get-information-schools.service.gov.uk/Downloads) | Open Government Licence v3.0 | British National Grid EPSG:27700 / EPSG:4326 | Open establishments in Bassetlaw from 17 November 2026 public download |

No AddressBase Premium, MasterMap premium, PSGA-only products, private Council records or commercial geocoding data are used.

## Exact extraction endpoints

- ONS district: `https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Local_Authority_Districts_December_2024_Boundaries_UK_BGC/FeatureServer/0/query` with `where=LAD24CD='E07000171'`, `outSR=4326`, `f=geojson`.
- ONS wards: `https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Wards_May_2024_Boundaries_UK_BSC/FeatureServer/0/query` with district bounding box, `inSR=4326`, `outSR=4326`, `f=geojson`. Retain polygons with representative point in the district plus 0.001-degree tolerance, accommodating differing source generalisation. Ward polygons are not clipped for area profiles.
- EA: `https://environment.data.gov.uk/spatialdata/flood-map-for-planning-flood-zones/ogc/features/v1/collections/Flood_Zones_2_3_Rivers_and_Sea/items` with district bounding box, `f=json`, `limit=1000`. Follow all returned `next` links until complete. Clip to district and simplify at 50 metres in EPSG:27700 and validate the resulting geometry.
- Brownfield: `https://data.bassetlaw.gov.uk/media/8744/bassetlaw-brownfield-register.csv`. Use supplied GeoX/GeoY representative-point coordinates, identifiers, names, planning status and record date. Do not invent site polygons or convert hectares into fictional boundaries.
- GIAS: supported public bulk-download form at `/Downloads`. Download the public ZIP and pass it to the ingestion command. A national ZIP is temporarily held in ignored `.cache/public-data/`; keep only open records with `DistrictAdministrative (code)=E07000171`, coordinates within district plus a small tolerance. Discard personal/contact fields. The pipeline retains URN, establishment name, phase, status-selection outcome, coordinates and update date.

## Rebuild and quality control

```powershell
python -m pip install requests shapely pyproj
python -m data_pipeline.download
# Reuse existing ignored source cache when inspecting the same snapshot
python -m data_pipeline.download --use-cache
python -m pytest data_pipeline/test_validate.py -q
# GIAS needs its official public bulk ZIP; use --gias-zip PATH if not cached.
```

The pipeline validates required and unique identifiers, non-empty and valid geometry, and WGS84 coordinate bounds before writing `data/data_quality_report.json`. Source geometry is repaired with Shapely `make_valid` before clipping; generalised flood geometry is repaired and validated again after transformation back to WGS84. Empty and non-polygon results are omitted. Flood polygons are generalised at 50m; small components can be removed and boundaries can move. This is a demonstration extract, not site-scale evidence. The report records exact output counts. Registry hashes allow a deployed snapshot to be matched to an extract. Downloads use HTTP timeouts; flood paging avoids silent first-page truncation. A run is not silently substituted with fabricated or random features if a source fails.

The application database loader is maintained in `backend/manage.py`; migrations define spatial indexes. The frontend's public snapshots and the PostGIS loader must consume the same GeoJSON files. EPSG:27700 is used for metric calculations. A source refresh must be reviewed and re-tested before deployment.

## Interpreting the evidence

**Boundaries:** these are historical generalised snapshots. They support demonstration and area context, not legal boundary determinations. Ward geometry is May 2024 and should not be labelled current electoral geography or silently joined to incompatible Census data.

**Flood:** the dataset covers present-day rivers and sea planning flood zones, ignoring defences. It is not a property-level flood assessment and excludes other sources of flooding. A point outside the displayed polygons means only that this snapshot shows no intersection. Never label it "no risk". Fifty-metre simplification and generalised district clipping add boundary uncertainty. Use the official Flood Map for Planning for actual decisions.

**Brownfield:** these are register representative points, not exact parcels or Local Plan allocations. A nearby point provides historical register context. It does not establish a selection is within a brownfield site, or that consent/availability is current. Individual record update dates can be much older than the catalogue page update. Do not infer current permissions from the snapshot.

**Services:** this is a deliberately bounded educational-establishment example. A straight-line nearest-school distance is neither a walking/driving journey nor an admissions/catchment statement. Counts include only loaded open establishments in the district, and can omit nearer facilities outside the district. School capacity, quality, place availability, demographic demand and population are not inferred.

**Community profiles:** derived area, mapped-school counts and school phase distribution are spatial summaries of this snapshot. No Census population, deprivation, housing need or accessibility score is invented.

## Attribution and licensing checks

- ONS [geography licensing](https://www.ons.gov.uk/methodology/geography/licences): "Source: Office for National Statistics licensed under the Open Government Licence v.3.0" and "Contains OS data © Crown copyright and database right 2024".
- EA catalogue states Open Government Licence and requests: "© Environment Agency copyright and/or database right 2025. All rights reserved."
- Bassetlaw [open-data licensing page](https://data.bassetlaw.gov.uk/information-pages/licensing-information/) covers published downloads under OGL and requires public-sector and OS attribution. Its interactive OS basemap is explicitly excluded from copying; this project uses only the downloadable register CSV.
- DfE [acceptable-use policy](https://get-information-schools.service.gov.uk/AcceptableUsePolicy) directs bulk use to public downloads. The public site footer supplies OGL attribution. The pipeline uses that download workflow rather than harvesting individual school pages.
- OGL reference: <https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/>.

## Investigated but excluded

Bassetlaw-hosted ArcGIS local-area and green-space layers were publicly readable but had no unambiguous redistribution licence metadata and included premium OS copyright notices. They were not copied. OS Open Greenspace was not loaded during this bounded implementation. Missing green-space or planning-allocation indicators must remain explicitly unavailable, never zero-risk or invented values. No project boundary for West Burton is fabricated; project context is supplied only via cited narrative unless a verifiable openly licensed geometry is later added.

## Disclaimer

Independent interview prototype by Victor Okeke. Not an official Bassetlaw District Council service.
