# Known data issues

## ACS 2020 experimental weights

The ACS 2020 1-year PUMS file uses experimental weights due to COVID-19
response disruption. Per the U.S. Census Bureau, do not directly compare
2020 to other years. This dashboard includes 2020 in the dataset for
transparency but the methodology page flags it prominently. The 2021 dip
also reflects pandemic labor-market disruption rather than baseline change.

Reference: <https://www.census.gov/programs-surveys/acs/technical-documentation/user-notes/2021-02.html>

## Pre-2005 ACS sample sizes

ACS 1-year samples for 2000–2004 are materially smaller than 2005+ samples
(50K–1M persons/year vs 3M+). Default dashboard time range is 2005–2024.
Pre-2005 data is included for users who expand the slicer; expect sparser
country-cohort cells in those years.

## BPL regional aggregations

IPUMS's harmonized BPL groups several regions to a single code:

- **Central America (BPL 210)** — Honduras, Guatemala, El Salvador,
  Nicaragua, Panama, Costa Rica, etc., all aggregated
- **South America (BPL 300)** — Brazil, Colombia, Peru, Venezuela,
  Argentina, Chile, etc., all aggregated
- **West Indies (BPL 260)** — Jamaica, Haiti, Dominican Republic, Trinidad,
  etc., all aggregated
- **Africa (BPL 600)** — all African countries aggregated to a single bucket

These appear in the dashboard with explicit "(region)" suffix to flag the
limitation. Country-level detail for these regions requires `BPLD` (the
detailed BPL variable), which is planned for v2.

## Sparse-tier countries

Countries with fewer than 25 cells of data (Cambodia, Greece, Lebanon,
Romania, Yugoslavia, Thailand, France) appear sparsely on charts — isolated
points rather than continuous trend lines. They are excluded from default
views but available via slicer override. The Comparison page leaderboard
excludes sparse-tier countries by default to avoid misleading rankings on
unstable medians.

## Country-of-origin consolidations

The aggregator combines:

- BPL 410 (England), 411 (Scotland), 412 (Wales) → 413 (United Kingdom)

And relabels for historical accuracy:

- BPL 452 → "Former Czechoslovakia"
- BPL 457 → "Former Yugoslavia"
- BPL 465 → "Former USSR / Russia"

See `docs/methodology.md` § *Country-of-origin consolidations* for rationale.

## Suppression threshold quirks

The N ≥ 200 unweighted threshold is applied **per cell**, not per country.
A country may have 50+ cells in aggregate but only some pass the threshold
in any given year × age × tenure combination. Visible "gaps" in trend lines
reflect this cell-level suppression, not missing data per se.