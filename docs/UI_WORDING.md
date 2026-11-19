# Evidence wording and scope

The interface names the datasets actually used, rather than implying that a bounded public-data prototype covers all planning constraints, council services or community needs.

| Previous wording | Current wording or treatment | Reason |
|---|---|---|
| Planning context / nearest mapped context point | Nearby brownfield register site | Only register representative points are included. Distance is to the supplied point, not the site boundary. Individual record dates are shown separately from download dates. |
| Flood / environment | River and sea flood zones | The loaded source is the Environment Agency planning flood-zone extract. Other environmental constraints and flood sources are not assessed. |
| Service proximity / nearest mapped feature | Nearby schools and colleges | The service extract consists of open educational-establishment records, including specialist providers. It is not a general council-service inventory. |
| Mapped service locations within 2 km | Schools and colleges in the loaded dataset within 2 km | Counts use a straight-line radius. Only the Bassetlaw extract is included. |
| Empty green-space / growth sections | Exclusions listed in Data & Method | An excluded dataset is different from a failed evidence request. Temporary failures remain visible beside the affected evidence. |
| Analysis mode: postgis / browser snapshot | Plain-language calculation labels | Database and browser calculations both use published snapshots; neither label implies a live provider feed. |
| Community evidence / service distribution | Ward education profile / schools and colleges by ward | This is a bounded education-establishment example, not a population, deprivation or complete accessibility profile. |
| Service categories | Removed redundant indicator; retain phase chart | The chart already explains phase distribution. “Not applicable” is retained as the source classification with a plain explanation. |
| Nearest service from ward reference point | Removed | The arbitrary reference point is not a population centre or a defensible community accessibility measure. |

Ward boundaries are explicitly dated May 2024. Data-source links show boundary/dataset/catalogue update dates and download dates separately. Unknown record dates are not invented. Distance appears once per result, with route, site-boundary, admissions and capacity limitations stated where relevant.

The community summary retains ward area and the count of included establishments. It shows a genuine zero only when the establishment dataset was successfully available and the ward subset was empty. Failed downloads yield unavailable evidence, not zero. Browser fallback and backend use the same labels, scope and phase field.
