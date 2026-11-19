# Bassetlaw facts used

The app presents extracted evidence, not a judgement about the Council's existing systems. These are the Bassetlaw-specific facts used in its working views:

- District name Bassetlaw and code E07000171: [Office for National Statistics December 2024 district geography](https://www.arcgis.com/home/item.html?id=6a05f93297cf4a438d08e972099f54b9). District shape is generalised and historical.
- Ward names/codes and polygons: [Office for National Statistics May 2024 ward geography](https://www.arcgis.com/home/item.html?id=b58c65bdad994ed3a33741eea7bb09ab). The extract has 25 wards; this is not asserted to be the current electoral geography.
- Flood-zone intersections: [Environment Agency Flood Map for Planning](https://www.data.gov.uk/dataset/104434b0-5263-4c90-9b1e-e43b1d57c750/flood-map-for-planning-flood-zones1), clipped without analytical simplification, with separate zoom-dependent display tiles. Results apply to this snapshot, not a property assessment.
- Historical brownfield-register context: [Bassetlaw downloadable register](https://data.bassetlaw.gov.uk/brownfield-register/), 31 representative points with their individual record dates. They are not parcel boundaries or current permission claims.
- Open mapped educational establishments: [Department for Education public bulk data](https://get-information-schools.service.gov.uk/Downloads), 61 records selected by district code, status and coordinates. Distances/counts are calculated, not source-provided accessibility measures.
- Public-site colour values: [Bassetlaw's own stylesheet](https://www.bassetlaw.gov.uk/css/Bassetlaw-District-Council-Min.css); observed values and selectors are documented in ../frontend/BRANDING.md. This is not a claim to reproduce a formal brand manual.

The prototype makes no claim about Bassetlaw's internal data quality, duplication, technology, integrations or GIS maturity. Local Government Reorganisation is discussed as a conceptual integration use case; no local outcome is predicted.

Spherical Tokamak for Energy Production (STEP) and West Burton were investigated, but no licensed verified project geometry was loaded. Consequently the app shows no strategic project boundary, jobs figure, investment estimate or timeline. Green-space and Census metrics are also absent rather than invented.

For complete extraction URLs, licences, fields, transformations and limitations see DATA_SOURCES.md and data/dataset_registry.json.
